class ChainDispatchResult(object):
    def __init__(self, table_name, chain_name=None, success=False,
                 chain_result=None,
                 block_results=None, chain_results=None, rvalue=None,
                 extraction_rule_results=None, outcome=False,
                 extraction_value=None, block_name=None):

        self.table_name = table_name
        self.extraction_rule_results = extraction_rule_results
        self.extraction_value = extraction_value
        self.chain_name = chain_name
        self.chain_outcome = outcome
        self.chain_rvalue = rvalue
        self.block_name = block_name
        self.block_results = block_results
        self.chain_result = chain_result
        self.outcome = outcome


    def get_chain_results(self):
        return self.chain_result

    def get_rule_results(self):
        if self.chain_result is not None:
            return self.chain_result.get_rule_results()
        return None

    def get_rule_name(self):
        if self.chain_result is not None:
            return self.chain_result.get_rule_name()
        return None

    def update_from_chain_result(self, chain_result):
        self.chain_name = chain_result.chain_name
        self.chain_result = chain_result
        self.chain_outcome = chain_result.outcome
        self.block_name = chain_result.block_name
        self.block_results = chain_result.block_results
        self.chain_rvalue = chain_result.rvalue
        self.outcome = chain_result.outcome


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
    def from_json(cls, json_data, block_objs={}, chains={}, chains_def={}):
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
        # print json_data.get('dispatch_table')
        for k, v in json_data.get('dispatch_table', []):
            c = chains.get(v, None)
            dispatch_table[k] = c

        return ChainDispatch(name, extract_rule, etype, evalue,
                             all_blocks=all_blocks, any_blocks=any_blocks,
                             none_blocks=none_blocks, blocks=blocks,
                             dispatch_table=dispatch_table,
                             perform_blocks=perform_blocks)

    def execute_value_extraction(self, string, frontend=None, state={}):
        frontend = frontend if frontend is not None else self.frontend
        results = frontend.match_pattern(self.extract_rule, string)
        value = self.extract_value(state, results.get('rule_results', {}))
        # print "value is: ", value
        return value, results

    def execute_dispatch(self, string, frontend=None, state={}):
        cdr = ChainDispatchResult(self.name)
        frontend = frontend if frontend is not None else self.frontend
        if frontend is None:
            raise Exception("Missing frontend reference")

        # TODO run a pre-check set of blocks or chains
        # before executing the value extraction

        value, rule_results = self.execute_value_extraction(string,
                                                            frontend, state)
        # print value, rule_results
        cdr.extraction_value = value
        cdr.extraction_rule_results = rule_results
        chains = self.dispatch_table.get(value, None)
        if chains is not None:
            chain_result = chains.execute_chains(string)
            cdr.update_from_chain_result(chain_result)

        return cdr

    def update_frontend(self, frontend):
        self.frontend = frontend
