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

class DescribeSecurityGroups(euca2ools.commands.eucacommand.EucaCommand):

    APIVersion = '2013-06-15'
    Description = 'Describe security groups.'
    Args = [Param(name='group_name', ptype='string',
                  doc='group(s) to describe',
                  cardinality='+', optional=True)]

    def display_groups(self, groups):
        for group in groups:
            print "\n"
            print '%-16s%-16s%-24s%-24s' % ("GroupId", "VpcId", "Name", "Description")
            print '%-16s%-16s%-24s%-24s' % ("-------", "-----", "----", "-----------")
            if group.vpc_id:
                print '%-16s%-16s%-24s%-24s' % (group.id, group.vpc_id, group.name, group.description)
            else:
                print '%-16s%-16s%-24s%-24s' % (group.id, "", group.name, group.description)
             
            print "\n"
            print '%-16s%-16s%-8s%-8s%-8s%-24s' % ("", "Direction", "Proto", "Start", "End", "Remote")
            print '%-16s%-16s%-8s%-8s%-8s%-24s' % ("", "---------", "-----", "-----", "---", "------")
            for rule in group.rules:
                if rule.ip_protocol == '-1':
                    rule.ip_protocol = 'any'
                print '%-16s%-16s%-8s%-8s%-8s%-24s' % ("", "Ingress", rule.ip_protocol, rule.from_port, rule.to_port, rule.grants)
            for rule in group.rules_egress:
                if rule.ip_protocol == '-1':
                    rule.ip_protocol = 'any'
                print '%-16s%-16s%-8s%-8s%-8s%-24s' % ("", "Egress", rule.ip_protocol, rule.from_port, rule.to_port, rule.grants)
        print "\n"

    def main(self):
        conn = self.make_connection_cli('vpc')
        return self.make_request_cli(conn, 'get_all_security_groups',
                                     groupnames=self.group_name)

    def main_cli(self):
        groups = self.main()
        self.display_groups(groups)
