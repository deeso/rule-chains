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

    def add_blocks(self, block_objs):
        for name, block in block_objs.items():
            self.blocks[name] = block

    def add_chain_dispatch_tables(self, dispatch_tables):
        for name, dispatch_table in dispatch_tables.items():
            self.dispatch_tables[name] = dispatch_table

    def execute_dispatch_tables(self, string):
        results = []
        success = False
        for name, dispatch_table in self.dispatch_tables.items():
            success, cdr = dispatch_table.execute_dispatch(string)
            results.append(cdr)
            if success:
                break
        return success, results

    def match_any(self, string, ignore_empty=True):
        success, cdr = self.execute_dispatch_tables(string)
        if success:
            chain_result = cdr.chain_rvalue
            return chain_result

        chain_rvalue = self.match_with_chains(string)
        if chain_rvalue is not None:
            return chain_rvalue

        success, pattern_name, results = self.match_any_pattern(string)
        return results

    def match_any_pattern(self, string, ignore_empty=True):
        for grok_name, grok in self.groks.items():
            v = grok.match(string)
            if v is not None and len(v) > 0:
                return True, grok_name, v
        return False, None, None

    def match_with_chains(self, string):
        for name, chain in self.chains.items():
            chain_result = chain.execute_chain(string)
            if chain_result.outcome:
                return chain_result.rvalue
        return None

    def match_pattern(self, pattern_name, string, ignore_empty=True):
        v = None
        if pattern_name in self.groks:
            grok = self.groks[pattern_name]
            v = grok.match(string)
            return v
        elif pattern_name in self.gr.predefined_patterns:
            p = self.get_pattern_regex(pattern_name)
            grok = pygrok.Grok(p, custom_patterns_dir=self.custom_patterns_dir)
            v = grok.match(string)
            return v
        self.fail("Pattern name: %s does not exist" % pattern_name)

    def match_runall_patterns(self, string, ignore_empty=True):
        results = {}
        for pattern, grok in self.groks.items():
            v = grok.match(string)
            if ignore_empty and (v is None or len(v) == 0):
                continue
            results[pattern] = v
        return results
