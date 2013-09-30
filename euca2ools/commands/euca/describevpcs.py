# Software License Agreement (BSD License)
#
# Copyright (c) 2009-2011, Eucalyptus Systems, Inc.
# All rights reserved.
#
# Redistribution and use of this software in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:
#
#   Redistributions of source code must retain the above
#   copyright notice, this list of conditions and the
#   following disclaimer.
#
#   Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the
#   following disclaimer in the documentation and/or other
#   materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Author: Neil Soman neil@eucalyptus.com
#         Mitch Garnaat mgarnaat@eucalyptus.com

import euca2ools.commands.eucacommand
from boto.roboto.param import Param

class DescribeVpcs(euca2ools.commands.eucacommand.EucaCommand):

    APIVersion = '2013-06-15'
    Description = 'Shows information about VPCs.'
    Options = [Param(name='all', short_name='a', long_name='all',
                     optional=True, ptype='boolean', default=False,
                     doc='Show all vpcs.')]
    Args = [Param(name='vpcid', ptype='string',
                  cardinality='+', optional=True)]
    
    Filters = [Param(name='cidrBlock', ptype='string',
                     doc = "The CIDR block of the VPC."),
               Param(name='state', ptype='string',
                     doc = "The state of the VPC.Valid values: pending | available"), 
               Param(name='dhcpOptionsId', ptype='string',
                     doc="The ID of a set of DHCP options.")]
    def display_vpcs(self, vpcs):
        print "%-16s%-16s%-16s" % ('VpcId', 'CidrBlock', 'DhcpOptions')
        print "%-16s%-16s%-16s" % ('-----', '---------', '-----------')
        for vpc in vpcs:
            print "%-16s%-16s%-16s" % (vpc.id, vpc.cidr_block, vpc.dhcp_options_id)

    def main(self):
        conn = self.make_connection_cli('vpc')
        vpcs = self.make_request_cli(conn, 'get_all_vpcs', vpc_ids=self.vpcid, filters=self.filters)
        return vpcs

    def main_cli(self):
        vpcs = self.main()
        self.display_vpcs(vpcs)
