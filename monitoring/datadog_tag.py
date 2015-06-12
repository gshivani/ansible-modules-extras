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
module: datadog_tag
short_description: Manages Datadog tags of hosts
description:
- "Manages tags of hosts within Datadog"
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
    host:
        description:["Tags of a particular host"]
        required: true
        default: null
    state: 
        description: ["The state of the tags"]
        required: true
        choices: ['present', 'absent']
    source:
        description: ["The source of the tags"]
        required: false
        default: null
    by_source:
        description: ["A boolean indicating whether tags returned are grouped by source"]
        required: false
        default: False
    tags: 
        description: ["Comma separated list of tags to apply to the host"]
        required: true
        default: null
'''

EXAMPLES = '''
# Adds tags
datadog_tag:
  host: "Test host"
  state: "present"
  tags: 'Tag1, Tag2' 
  api_key: "key"
  app_key: "app_key"

# Deletes all tags 
datadog_tag:
  host: "Test host"
  state: "absent"
  api_key: "key"
  app_key: "app_key"

'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_key=dict(required=True),
            app_key=dict(required=True),
            host=dict(required=True),
            state=dict(required=True, choices=['present', 'absent']),
            source=dict(required=False, default=None),
            by_source=dict(required=False, default=False, choices=BOOLEANS),
            tags=dict(required=False, default=None)
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
    
    
    if module.params['state'] == 'present':
        add_tags(module)
    elif module.params['state'] == 'absent':
        delete_tags(module)

   
def _get_tags(module):
        hosts = api.Infrastructure.search(q=module.params['host'])
        tags = api.Tag.get(hosts['results']['hosts'][0], by_source=module.boolean(module.params['by_source']), 
                          source=module.params['source'])
        return tags
                                
def _create_tags(module):
    try:       
        hosts = api.Infrastructure.search(q=module.params['host'])
        msg = api.Tag.create(hosts['results']['hosts'][0], tags=module.params['tags'].split(), 
                            source=module.params['source'])   
        if 'errors' in msg:
            module.fail_json(msg=str(msg['errors']))
        else:
            module.exit_json(changed=True, msg=msg)
    except Exception, e:
        module.fail_json(msg=str(e))

def _update_tags(module):
    try:
        msg = api.Tag.update(module.params['host'], tags=module.params['tags'].split(), 
                            source=module.params['source'])
        if 'errors' in msg:
            module.fail_json(msg=str(msg['errors']))
        else:
            module.exit_json(changed=True, msg=msg)
    except Exception, e:
        module.fail_json(msg=str(e))


def add_tags(module):
        
        tags = _get_tags(module)
        if not tags:
            _create_tags(module)
        else:
            _update_tags(module)
            
            
def delete_tags(module):
    try:
        msg = api.Tag.delete(module.params['host'], source=module.params['source'])
        module.exit_json(changed=True, msg=msg)
    except Exception, e:
        module.fail_json(msg=str(e))


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
main()
