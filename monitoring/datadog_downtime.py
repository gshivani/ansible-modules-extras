#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Shivani Gowrishankar <s.gowrishankar@ntoggle.com>
#

# Import Datadog
try:
    from datadog import initialize, api
    HAS_DATADOG = True
except:
    HAS_DATADOG = False

DOCUMENTATION = '''
---
module: datadog_downtime
short_description: Manages Datadog downtimes of monitors
description:
- "Manages Datadog downtimes of monitors"
- "Options like described on http://docs.datadoghq.com/api/"
version_added: "2.0"
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
        description: ["The scope to apply the downtime"]
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
  scope: "Test monitor"
  state: "present"
  message: "Some message."
  api_key: "key"
  app_key: "app_key"

# Cancels a downtime for monitor
datadog_downtime:
  scope: "Test monitor"
  state: "absent"
  message: "Some message."
  api_key: "key"
  app_key: "app_key"
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_key=dict(required=True),
            app_key=dict(required=True),
            state=dict(required=True, choices=['present', 'absent']),
            scope=dict(required=True),
            start=dict(required=False, default=None),
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
    scope = [module.params['scope']]
    for downtime in api.Downtime.get_all(current_only=module.params['current_only']):
        if downtime['scope'] == scope:
            stagingDowntimes.append(downtime)      
    return stagingDowntimes
            
 
def _create_downtime(module):
    try:
        msg = api.Downtime.create(scope=module.params['scope'], start=module.params['start'],
                                  end=module.params['end'], message=module.params['message'])
        if 'errors' in msg:
            module.fail_json(msg=str(msg['errors']))
        else:
            module.exit_json(changed=True, msg=msg)
    except Exception, e:
        module.fail_json(msg=str(e))


def _update_downtime(module, downtimes):
    try:
        msg = api.Downtime.update(downtimes[0]['id'], scope=module.params['scope'], start=module.params['start'],
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
            msg = api.Downtime.delete(downtime['id'])
        module.exit_json(changed=True, msg="Downtime for scope '%s' cancelled." % (module.params['scope']))
    except Exception, e:
        module.fail_json(msg=str(e))
            

from ansible.module_utils.basic import *

main()
