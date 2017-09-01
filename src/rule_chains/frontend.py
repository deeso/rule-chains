import pygrok
from parse import ParseRuleChainsConfig


class BaseFrontend(object):
    def load_from_config(self):
        raise Exception("Not implemented")

    def load_rule_by_name_from_frontend(self, pattern_name):
        raise Exception("Not implemented")

    def load_rule_from_frontend(self, pattern):
        raise Exception("Not implemented")

    def get_pattern_regex(self, pattern_name):
        raise Exception("Not implemented")

    def is_pattern_available(self, pattern_name):
        raise Exception("Not implemented")

    def has_pattern(self, pattern_name):
        raise Exception("Not implemented")

    def is_predefined_pattern(self, pattern_name):
        raise Exception("Not implemented")

    def add_chain_definitions(self, chain_defs_objs):
        raise Exception("Not implemented")

    def add_groups(self, groups_data):
        raise Exception("Not implemented")

    def add_blocks(self, block_objs):
        raise Exception("Not implemented")

    def add_chain_dispatch_tables(self, dispatch_tables):
        raise Exception("Not implemented")

    def execute_dispatch_tables(self, string):
        raise Exception("Not implemented")

    def match_any(self, string, ignore_empty=True):
        raise Exception("Not implemented")

    def match_any_pattern(self, string, ignore_empty=True):
        raise Exception("Not implemented")

    def match_with_chains(self, string):
        raise Exception("Not implemented")

    def match_pattern(self, pattern_name, string, ignore_empty=True):
        raise Exception("Not implemented")

    def match_runall_patterns(self, string, ignore_empty=True):
        raise Exception("Not implemented")

    def fail(self, msg):
        raise Exception(msg)


class GrokFrontend(BaseFrontend):
    def __init__(self, config=None, custom_patterns_dir=None,
                 patterns_names=None):
        self.chain_definitions = {}
        self.grok_groups = {}
        self.blocks = {}
        self.dispatch_tables = {}
        self.program_matches = {}
        self.groks = {}
        self.chains = {}

        self.gr = pygrok.Grok('dummy', custom_patterns_dir=custom_patterns_dir)
        self.loaded_patterns = self.gr.predefined_patterns
        self.custom_patterns_dir = custom_patterns_dir

        # load all the grok patterns
        if patterns_names is not None:
            lines = [i.strip() for i in open(patterns_names).readlines()
                     if len(i.strip()) > 0]
            for line in lines:
                pattern_name = line
                self.load_rule_from_frontend(pattern_name)

        if config is not None:
            self.config = config
            self.load_from_config()

    def load_from_config(self):
        return ParseRuleChainsConfig.parse(self.config, frontend=self)

    def load_rule_from_frontend(self, pattern_name):
        if self.is_pattern_available(pattern_name):
            return True
        if self.has_pattern(pattern_name):
            grok = self.load_grok_by_pattern_name(pattern_name)
            if grok is not None:
                return True
        return False

    def load_grok_by_pattern_name(self, pattern_name):
        pattern = self.get_pattern_regex(pattern_name)
        return self.load_grok(pattern_name, pattern)

    def load_grok(self, pattern_name, pattern):
        pg = pygrok.Grok(pattern,
                         custom_patterns_dir=self.custom_patterns_dir)
        self.groks[pattern_name] = pg
        return pg

    def get_pattern_regex(self, pattern_name):
        if self.is_pattern_available(pattern_name):
            return self.groks[pattern_name].pattern
        elif self.has_pattern(pattern_name):
            return self.loaded_patterns[pattern_name].regex_str
        return None

    def is_pattern_available(self, pattern_name):
        return pattern_name in self.groks

    def has_pattern(self, pattern_name):
        return self.is_pattern_available(pattern_name) or \
               self.is_predefined_pattern(pattern_name)

    def is_predefined_pattern(self, pattern_name):
        return pattern_name in self.gr.predefined_patterns

    def add_chain_definitions(self, chain_defs_objs):
        for name, chain_definition in chain_defs_objs.items():
            self.chain_definitions[name] = chain_definition

    def add_groups(self, groups_data):
        s = "Unable to load %s, no corresponding regular expression"
        for name, pattern_names in groups_data.items():
            self.grok_groups[name] = []
            for pattern_name in pattern_names:
                grok = self.load_grok_by_pattern_name(pattern_name)
                if grok is None:
                    msg = s % pattern_name
                    self.fail(msg)
                self.grok_groups[name].append(pattern_name)

    def add_chains(self, chain_objs={}):
        for name, chain in chain_objs.items():
            # chain.update_frontend(self)
            self.chains[name] = chain

    def add_blocks(self, block_objs):
        for name, block in block_objs.items():
            block.update_frontend(self)
            self.blocks[name] = block

    def add_chain_dispatch_tables(self, dispatch_tables):
        for name, dispatch_table in dispatch_tables.items():
            dispatch_table.update_frontend(self)
            self.dispatch_tables[name] = dispatch_table

    def execute_dispatch_tables(self, string):
        results = {'outcome': False,
                   'rule_results': None,
                   'rule_name': None,
                   'dispatch_results': []}
        success = False
        for name, dispatch_table in self.dispatch_tables.items():
            cdr = dispatch_table.execute_dispatch(string)
            results['dispatch_results'].append(cdr)
            if success:
                results['outcome'] = True
                results['rule_name'] = cdr.get_rule_name()
                results['rule_results'] = cdr.get_rule_results()
                break
        return results

    def match_any(self, string, ignore_empty=True):
        results = self.execute_dispatch_tables(string)
        if results['outcome']:
            results['type'] = 'dispatcher'
            return results

        results = self.match_with_chains(string)
        if results['outcome']:
            results['type'] = 'chains'
            return results

        results = self.match_any_pattern(string)
        if results['outcome']:
            results['type'] = 'pattern'
        else:
            results['type'] = None
        return results

    def match_any_pattern(self, string, ignore_empty=True):
        results = {'outcome': False,
                   'rule_results': None,
                   'rule_name': None}
        for grok_name, grok in self.groks.items():
            v = grok.match(string)
            if v is not None and len(v) > 0:
                results['rule_name'] = grok_name
                results['rule_results'] = v
                results['outcome'] = True
                return results
        return results

    def match_with_chains(self, string):
        results = {'outcome': False,
                   'rule_results': None,
                   'rule_name': None,
                   'chain_result': None}
        chain_result = None
        for name, chain in self.chains.items():
            chain_result = chain.execute_chain(string)
            if chain_result.outcome:
                results['outcome'] = chain_result.outcome
                results['rule_results'] = chain_result.get_rule_results()
                results['rule_name'] = chain_result.get_rule_name()
                results['chain_result'] = chain_result
                return results
        return results

    def match_pattern(self, pattern_name, string, ignore_empty=True):
        results = {'outcome': False,
                   'rule_results': None,
                   'rule_name': pattern_name}
        if pattern_name in self.groks:
            grok = self.groks[pattern_name]
            results['rule_results'] = grok.match(string)
            results['outcome'] = results['rule_results'] is not None and \
                len(results['rule_results']) > 0
            return results
        elif pattern_name in self.gr.predefined_patterns:
            p = self.get_pattern_regex(pattern_name)
            grok = pygrok.Grok(p, custom_patterns_dir=self.custom_patterns_dir)
            results['rule_results'] = grok.match(string)
            results['outcome'] = results['rule_results'] is not None and \
                len(results['rule_results']) > 0
            return results
        return results

    def match_runall_patterns(self, string, ignore_empty=True):
        all_results = {}
        for pattern_name in self.groks.keys():
            results = self.match_pattern(pattern_name, string)
            if ignore_empty and results['outcome'] is False:
                continue
            all_results[pattern_name] = results
        return all_results
