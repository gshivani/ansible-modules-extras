#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Shivani Gowrishankar <s.gowrishankar@ntoggle.com>
#
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: datadog_downtime
short_description: Manages Datadog downtimes of monitors
description:
- "Manages Datadog downtimes of monitors"
- "Options like described on http://docs.datadoghq.com/api/"
version_added: "2.1"
author: '"Shivani Gowrishankar" <s.gowrishankar@ntoggle.com>'
notes: []
requirements: [datadog]
options:
    api_key:
        description: ["Your DataDog API key."]
        required: true
    app_key:
        description: ["Your DataDog app key."]
        required: true
    state:
        description: ["The designated state of the monitor."]
        required: true
        choices: ['present', 'absent']
    scope:
        description: ["The tag scopes to apply the downtime to, comma seperated."]
        required: true
    start:
        description: ["POSIX timestamp to start the downtime"]
        required: false
        default: null
    end:
        description: ["POSIX timestamp to end the downtime"]
        required: false
        default: null
    message:
        description: ["A message to include with notifications for the downtime"]
        required: false
        default: null
    id:
        description: ["The integer id of the downtime to be updated"]
        required: false
    current_only:
        description: ["Only return downtimes that are active when the request is made"]
        required: false
        default: False
'''

EXAMPLES = '''
# Schedule a downtime for monitor
datadog_downtime:
  scope: "test:tag,test2:tag"
  state: "present"
  message: "Some message."
  api_key: "key"
  app_key: "app_key"

# Cancels a downtime for monitor
datadog_downtime:
  scope: "test:tag,test2:tag"
  state: "absent"
  message: "Some message."
  api_key: "key"
  app_key: "app_key"
'''

RETURN = '''
changed:
    description: A flag indicating if any change was made or not.
    returned: success
    type: boolean
    sample: True
'''

# Import Datadog
try:
    from datadog import initialize, api
    HAS_DATADOG = True
except:
    HAS_DATADOG = False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_key=dict(required=True),
            app_key=dict(required=True),
            state=dict(required=True, choices=['present', 'absent']),
            scope=dict(required=True),
            start=dict(required=False, default=None, type='list'),
            end=dict(requried=False, default=None),
            message=dict(required=False, default=None),
            id=dict(required=False),
            current_only=dict(required=False, default=False),
        )
    )

    # Prepare Datadog
    if not HAS_DATADOG:
        module.fail_json(msg='datadogpy required for this module')

    options = {
        'api_key': module.params['api_key'],
        'app_key': module.params['app_key']
    }

    initialize(**options)

    downtimes = _get_downtime(module)
    if module.params['state'] == 'present':
        schedule_downtime(module, downtimes)
    elif module.params['state'] == 'absent':
        cancel_downtime(module, downtimes)


def _get_downtime(module):
    stagingDowntimes = []
    scopes = module.params['scope'].split(',')
    for downtime in api.Downtime.get_all(current_only=module.params['current_only']):
        for scope in scopes:
            if scope in downtime['scope']:
                stagingDowntimes.append(downtime)
    return stagingDowntimes


def _create_downtime(module):
    try:
        scopes = module.params['scope'].split(',')
        msg = api.Downtime.create(scope=scopes, start=module.params['start'],
                                  end=module.params['end'], message=module.params['message'])
        if 'errors' in msg:
            module.fail_json(msg=str(msg['errors']))
        else:
            module.exit_json(changed=True, msg=msg)
    except Exception, e:
        module.fail_json(msg=str(e))


def _update_downtime(module, downtimes):
    try:
        scopes = module.params['scope'].split(',')
        msg = api.Downtime.update(downtimes[0]['id'], scope=scopes, start=module.params['start'],
                                  end=module.params['end'], message=module.params['message'])
        if 'errors' in msg:
            module.fail_json(msg=str(msg['errors']))
        else:
            module.exit_json(changed=True, msg=msg)
    except Exception, e:
        module.fail_json(msg=str(e))


def schedule_downtime(module, downtimes):
    if not downtimes:
        _create_downtime(module)
    else:
        _update_downtime(module, downtimes)


def cancel_downtime(module, downtimes):
    try:
        for downtime in downtimes:
            api.Downtime.delete(downtime['id'])
        module.exit_json(changed=True, msg="Downtime for scope '%s' cancelled." % (module.params['scope']))
    except Exception, e:
        module.fail_json(msg=str(e))


from ansible.module_utils.basic import *
main()
