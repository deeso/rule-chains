class ChainDispatchResult(object):
    def __init__(self, table_name, chain_name=None, success=False,
                 chain_result=None,
                 block_results=None, chain_results=None, rvalue=None,
                 rule_results=None, chain=None, outcome=False,
                 extraction_value=None, last_block=None):

        self.chain = chain
        self.table_name = table_name
        self.rule_results = rule_results
        self.extraction_value = extraction_value
        self.chain_name = chain_name
        self.chain_outcome = outcome
        self.chain_rvalue = rvalue
        self.last_block = last_block
        self.block_results = block_results
        self.chain_result = chain_result
        self.outcome = outcome

    def get_chain_result(self):
        return self.chain_result

    def get_rule_result(self):
        if self.chain_result is not None:
            return self.chain_result.get_rule_result()
        return None

    def get_rule_name(self):
        if self.chain_result is not None:
            return self.chain_result.get_rule_name()
        return None

    def get_chain_result(self):
        return self.chain_result


class ChainDispatch(object):
    def __init__(self, name, extract_rule, extract_type, extract_value,
                 all_blocks=[], any_blocks=[], none_blocks=[], blocks=[],
                 dispatch_table={}, perform_blocks=None):

        self.name = name
        self.extract_rule = extract_rule
        self.dispatch_table = dispatch_table
        self.raw_value = extract_value
        self.perform_blocks = perform_blocks
        self.blocks = blocks
        self.all_blocks = all_blocks
        self.any_blocks = any_blocks
        self.none_blocks = none_blocks
        self.extract_value = self.code_factory(extract_type, extract_value)

    @classmethod
    def code_factory(cls, ctype, cvalue):
        if ctype == 'lambda':
            return eval(cvalue)
        elif ctype == 'function':
            return eval(cvalue)
        return lambda state, res: None

    @classmethod
    def from_json(cls, json_data, block_objs={}, chains={}):
        name = json_data.get('name', None)
        extract_rule = json_data.get('extract_rule', None)
        etype = json_data.get('extract_type', None)
        evalue = json_data.get('extract_value', None)
        any_blocks = json_data.get('any', [])
        all_blocks = json_data.get('all', [])
        none_blocks = json_data.get('none', [])
        _blocks = any_blocks + all_blocks + none_blocks
        blocks = dict((c, block_objs.get(c)) for c in _blocks
                      if c in block_objs)

        perform_blocks = json_data.get('perform_blocks', [])
        # print name, extract_rule, etype, evalue
        if name is None or \
           extract_rule is None or \
           etype is None or \
           evalue is None:
            raise Exception("Missing required Block parameters")

        dispatch_table = {}
        for k, v in json_data.get('dispatch_table', []):
            c = chains.get(v, None)
            dispatch_table[k] = c

        return ChainDispatch(name, extract_rule, etype, evalue,
                             all_blocks=all_blocks, any_blocks=any_blocks,
                             none_blocks=none_blocks, blocks=blocks,
                             dispatch_table=dispatch_table,
                             perform_blocks=perform_blocks)

    def execute_value_extraction(self, string, frontend):
        rule_results = frontend.match_pattern(self.extract_rule, string)
        value = self.extract_value(rule_results)
        return value, rule_results

    def execute_dispatch(self, string, frontend=None):
        cdr = ChainDispatchResult(self.name)
        if frontend is None:
            raise Exception("Missing frontend reference")

        # TODO run a pre-check set of blocks or chains
        # before executing the value extraction

        value, rule_results = self.execute_value_extraction(string, frontend)
        cdr.extraction_value = value
        cdr.rule_results = rule_results

        if value in self.value_chain_map:
            chains = self.value_chain_map[value]
            chain_result = chains.execute_chains(string)
            cdr.chain_result = chain_result
            cdr.chain_name = chain_result.chain
            cdr.block_results = chain_result.block_results
            cdr.chain_outcome = chain_result.outcome
            cdr.last_block = chain_result.block_results.last_block
            cdr.chain_rvalue = chain_result.rvalue
        return cdr
