# Copyright 2013-2015 Eucalyptus Systems, Inc.
#
# Redistribution and use of this software in source and binary forms,
# with or without modification, are permitted provided that the following
# conditions are met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os.path
import tarfile

from requestbuilder.command import BaseCommand
from requestbuilder.mixins import (FileTransferProgressBarMixin,
                                   RegionConfigurableMixin)

import euca2ools.bundle.manifest
from euca2ools.bundle.pipes.core import (create_bundle_pipeline,
                                         copy_with_progressbar)
from euca2ools.bundle.pipes.fittings import (create_bundle_part_writer,
                                             create_mpconn_aggregator)
import euca2ools.bundle.util
from euca2ools.commands import Euca2ools
from euca2ools.commands.bundle.mixins import BundleCreatingMixin
from euca2ools.commands.empyrean import EmpyreanRequest
from euca2ools.util import mkdtemp_for_large_files


class BundleImage(BaseCommand, BundleCreatingMixin,
                  FileTransferProgressBarMixin,
                  RegionConfigurableMixin):
    SUITE = Euca2ools
    DESCRIPTION = 'Prepare an image for use in the cloud'
    REGION_ENVVAR = 'AWS_DEFAULT_REGION'
    # Needed because BundleImage has no auth class of its own
    ARGS = EmpyreanRequest.AUTH_CLASS.ARGS

    # noinspection PyExceptionInherit
    def configure(self):
        self.update_config_view()

        BaseCommand.configure(self)

        # Set up access to empyrean in case we need auto cert fetching.
        #
        # We would normally make short work of this using from_other
        # methods, but since BundleImage doesn't have service or
        # auth classes of its own we get to do this the hard way.
        if not self.args.get('empyrean_service'):
            service = EmpyreanRequest.SERVICE_CLASS(
                config=self.config, loglevel=self.log.level,
                url=self.args.get('empyrean_url'))
            try:
                service.configure()
            except:
                self.log.debug('empyrean service setup failed; auto cert '
                               'fetching will be unavailable', exc_info=True)
            else:
                self.args['empyrean_service'] = service
        if (not self.args.get('empyrean_auth') and
                self.args.get('empyrean_service')):
            auth = EmpyreanRequest.AUTH_CLASS(
                config=self.config, loglevel=self.log.level, **self.args)
            try:
                auth.configure()
            except:
                self.log.debug('empyrean auth setup failed; auto cert '
                               'fetching will be unavailable', exc_info=True)
            else:
                self.args['empyrean_auth'] = auth

        self.configure_bundle_creds()
        self.configure_bundle_properties()
        self.configure_bundle_output()
        self.generate_encryption_keys()

    def main(self):
        if self.args.get('destination'):
            path_prefix = os.path.join(self.args['destination'],
                                       self.args['prefix'])
            if not os.path.exists(self.args['destination']):
                os.mkdir(self.args['destination'])
        else:
            tempdir = mkdtemp_for_large_files(prefix='bundle-')
            path_prefix = os.path.join(tempdir, self.args['prefix'])
        self.log.debug('bundle path prefix: %s', path_prefix)

        # First create the bundle
        digest, partinfo = self.create_bundle(path_prefix)

        # All done; now build the manifest and write it to disk
        manifest = self.build_manifest(digest, partinfo)
        manifest_filename = '{0}.manifest.xml'.format(path_prefix)
        with open(manifest_filename, 'w') as manifest_file:
            manifest.dump_to_file(manifest_file, self.args['privatekey'],
                                  self.args['cert'], self.args['ec2cert'])

        # Then we just inform the caller of all the files we wrote.
        # Manifests are returned in a tuple for future expansion, where we
        # bundle for more than one region at a time.
        return (part.filename for part in partinfo), (manifest_filename,)

    def print_result(self, result):
        for manifest_filename in result[1]:
            print 'Wrote manifest', manifest_filename

    def create_bundle(self, path_prefix):
        # Fill out all the relevant info needed for a tarball
        tarinfo = tarfile.TarInfo(self.args['prefix'])
        tarinfo.size = self.args['image_size']

        # The pipeline begins with self.args['image'] feeding a bundling pipe
        # segment through a progress meter, which has to happen on the main
        # thread, so we add that to the pipeline last.

        # meter --(bytes)--> bundler
        bundle_in_r, bundle_in_w = euca2ools.bundle.util.open_pipe_fileobjs()
        partwriter_in_r, partwriter_in_w = \
            euca2ools.bundle.util.open_pipe_fileobjs()
        digest_result_mpconn = create_bundle_pipeline(
            bundle_in_r, partwriter_in_w, self.args['enc_key'],
            self.args['enc_iv'], tarinfo, debug=self.debug)
        bundle_in_r.close()
        partwriter_in_w.close()

        # bundler --(bytes)-> part writer
        bundle_partinfo_mpconn = create_bundle_part_writer(
            partwriter_in_r, path_prefix, self.args['part_size'],
            debug=self.debug)
        partwriter_in_r.close()

        # part writer --(part info)-> part info aggregator
        # (needed for building the manifest)
        bundle_partinfo_aggr_mpconn = create_mpconn_aggregator(
            bundle_partinfo_mpconn, debug=self.debug)
        bundle_partinfo_mpconn.close()

        # disk --(bytes)-> bundler
        # (synchronous)
        label = self.args.get('progressbar_label') or 'Bundling image'
        pbar = self.get_progressbar(label=label,
                                    maxval=self.args['image_size'])
        with self.args['image'] as image:
            try:
                read_size = copy_with_progressbar(image, bundle_in_w,
                                                  progressbar=pbar)
            except ValueError:
                self.log.debug('error from copy_with_progressbar',
                               exc_info=True)
                raise RuntimeError('corrupt bundle: input size was larger '
                                   'than expected image size of {0}'
                                   .format(self.args['image_size']))
        bundle_in_w.close()
        if read_size != self.args['image_size']:
            raise RuntimeError('corrupt bundle: input size did not match '
                               'expected image size  (expected size: {0}, '
                               'read: {1})'
                               .format(self.args['image_size'], read_size))

        # All done; now grab info about the bundle we just created
        try:
            digest = digest_result_mpconn.recv()
            partinfo = bundle_partinfo_aggr_mpconn.recv()
        except EOFError:
            self.log.debug('EOFError from reading bundle info', exc_info=True)
            raise RuntimeError(
                'corrupt bundle: bundle process was interrupted')
        finally:
            digest_result_mpconn.close()
            bundle_partinfo_aggr_mpconn.close()
        self.log.info('%i bundle parts written to %s', len(partinfo),
                      os.path.dirname(path_prefix))
        self.log.debug('bundle digest: %s', digest)
        return digest, partinfo
