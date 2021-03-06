from . import Plugin


class CollectdPlugin(Plugin):
    def __init__(self, config):
        if hasattr(config, 'collectd_prefix'):
            prefix = config.collectd_prefix
        else:
            prefix = '^collectd\.'

        self.targets = [
            {
                'match': prefix + '(?P<server>[^\.]+)\.(?P<collectd_plugin>cpu)\.(?P<core>[^\.]+)\.cpu\.(?P<type>[^\.]+)$',
                'target_type': 'gauge_pct',
                'configure': lambda self, target: self.add_tag(target, 'unit', 'cpu_state')
            },
            {
                'match': prefix + '(?P<server>.+?)\.(?P<collectd_plugin>load)\.load\.(?P<wt>.*)$',
                'target_type': 'gauge',
                'configure': lambda self, target: self.fix_load(target)
            },
            {
                'match': prefix + '(?P<server>[^\.]+)\.interface\.(?P<interface>[^\.]+)\.if_(?P<wt>[^\.]+)\.(?P<dir>[^\.]+)$',
                'target_type': 'counter',
                'configure': [
                    lambda self, target: self.add_tag(target, 'collectd_plugin', 'network'),
                    lambda self, target: self.fix_network(target)
                ]
            },
            {
                'match': prefix + '(?P<server>[^\.]+)\.memory\.memory\.(?P<type>[^\.]+)$',
                'target_type': 'gauge',
                'configure': [
                    lambda self, target: self.add_tag(target, 'unit', 'B'),
                    lambda self, target: self.add_tag(target, 'where', 'system_memory')
                ]
            },
            {
                'match': prefix + '(?P<server>[^\.]+)\.(?P<collectd_plugin>disk)\.(?P<device>[^\.]+)\.disk_(?P<wt>[^\.]+)\.(?P<operation>[^\.]+)$',
                'configure': lambda self, target: self.fix_disk(target)
            }
        ]
        super(CollectdPlugin, self).__init__(config)

    def fix_disk(self, target):
        wt = {
            'merged': {
                'unit': 'Req',
                'type': 'merged'
            },
            'octets': {
                'unit': 'B'
            },
            'ops': {
                'unit': 'Req',
                'type': 'executed'
            },
            'time': {
                'unit': 'ms'
            }
        }
        target['tags'].update(wt[target['tags']['wt']])

        if self.config.collectd_StoreRates:
            target['tags']['target_type'] = 'rate'
            target['tags']['unit'] = target['tags']['unit'] + "/s"
        else:
            target['tags']['target_type'] = 'counter'

        del target['tags']['wt']

    def fix_load(self, target):
        human_to_computer = {
            'shortterm': '01',
            'midterm': '05',
            'longterm': '15'
        }
        target['tags']['unit'] = 'load'
        target['tags']['type'] = human_to_computer.get(target['tags']['wt'], 'unknown')
        del target['tags']['wt']

    def fix_network(self, target):
        dirs = {'rx': 'in', 'tx': 'out'}
        units = {'packets': 'Pckt', 'errors': 'Err', 'octets': 'B'}

        if self.config.collectd_StoreRates:
            target['tags']['target_type'] = 'rate'
            target['tags']['unit'] = units[target['tags']['wt']] + "/s"
        else:
            target['tags']['target_type'] = 'counter'
            target['tags']['unit'] = units[target['tags']['wt']]

        target['tags']['direction'] = dirs[target['tags']['dir']]
        del target['tags']['wt']
        del target['tags']['dir']

# vim: ts=4 et sw=4:
