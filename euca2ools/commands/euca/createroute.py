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

class CreateRoute(euca2ools.commands.eucacommand.EucaCommand):

    APIVersion = '2013-06-15'
    Description = """Creates a route in a route table within a VPC"""

    Args = [Param(name='route_table_id', ptype='string', optional=False,
                  doc='The ID of the route table for the route')]

    Options = [Param(name='cidr', ptype='string', optional=False,
                  doc='The CIDR address block used for the destination match',
                  short_name='r', long_name='cidr'),
               Param(name='gateway_id', ptype='string', optional=True,
                  doc='The ID of a gateway in your VPC',
                  short_name='g', long_name='gateway'),
               Param(name='instance_id', ptype='string', optional=True,
                  doc='The ID of a NAT instance in your VPC',
                  short_name='i', long_name='instance')]

    def main(self):
        conn = self.make_connection_cli('vpc')
        return self.make_request_cli(conn, 'create_route',
                                     route_table_id=self.route_table_id,
                                     destination_cidr_block=self.cidr,
                                     gateway_id=self.gateway_id,
                                     instance_id=self.instance_id)

    def main_cli(self):
        status = self.main()
        if status:
            idprint = ''
            if self.gateway_id: idprint = self.gateway_id
            elif self.instance_id: idprint = self.instance_id
            print "ROUTE\t%s\t%s" % (idprint , self.cidr)
        else:
            self.error_exit()

