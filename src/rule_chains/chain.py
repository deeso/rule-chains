class ChainResult(object):
    def __init__(self, chain=None, block_result=None,
                 outcome=None, rvalue=None, block_results=None):
        self.chain = chain
        self.block_result = block_result
        self.outcome = outcome
        self.rvalue = rvalue
        self.block_results = block_results

class Chain(object):
    def __init__(self, name, block_objs={}, blocks=[], all_blocks=[],
                 any_blocks=[], none_blocks=[],
                 perform_blocks=['blocks', 'all', 'any', 'none'],
                 frontend=None):

        self.name = name
        self.perform_blocks = perform_blocks
        self.frontend = frontend
        self.blocks = blocks
        self.all_blocks = all_blocks
        self.any_blocks = any_blocks
        self.none_blocks = none_blocks

    def serialize(self):
        results = {
            'name': self.name,
            'perform_blocks': self.perform_blocks,
            'blocks': self.blocks,
            'all_blocks': self.all_blocks,
            'any_blocks': self.any_blocks,
            'none_blocks': self.none_blocks,
        }
        if len(self.all_blocks) == 0:
            del results['all_blocks']
        if len(self.blocks) == 0:
            del results['blocks']
        if len(self.any_blocks) == 0:
            del results['any_blocks']
        if len(self.none_blocks) == 0:
            del results['none_blocks']
        return results

    def execute_block(self, name, string, state, save_key):
        obj = self.blocks.get(name, None)
        if obj is None:
            raise Exception("Block does not exist in %s chain." % self.name)

        block_save_key = "%s:%s:%s" % (save_key, self.name, name)
        block_result = obj.execute(string, state, self.frontend,
                                   block_save_key)
        return block_result

    def run_blocks(self, string, state, save_key):
        block_results = {'save_keys': []}
        for c in self.blocks:
            block_result = self.execute_block(c, string, state, save_key)
            br = block_result
            block_results[c] = block_result
            if br.doret or br.exit_on_fail:
                return c, block_results
        return c, block_results

    def run_all_blocks(self, string, state, save_key):
        block_results = {}
        for c in self.all_blocks:
            block_result = self.execute_block(c, string, state, save_key)
            br = block_result
            block_results[c] = block_result
            if br.doret or br.exit_on_fail or \
               isinstance(br.block_result, bool) and not br.block_result:
                return c, block_results
        return c, block_results

    def run_any_blocks(self, string, state, save_key):
        block_results = {}
        for c in self.blocks:
            block_result = self.execute_block(c, string, state, save_key)
            block_results[c] = block_result
            br = block_result
            if br.doret or br.exit_on_fail or \
               isinstance(br.block_result, bool) and br.block_result:
                return c, block_results
        return c, block_results

    def run_none_blocks(self, string, state, save_key):
        block_results = {}
        for c in self.none_blocks:
            block_result = self.execute_block(c, string, state, save_key)
            block_results[c] = block_result
            br = block_result
            if br.doret or br.exit_on_fail or \
               isinstance(br.block_result, bool) and br.block_result:
                return c, block_results
        return c, block_results

    def execute_chain(self, string, state={}):
        last_block = None
        block_result = None
        outcome = False
        doret = False
        exit = False
        rvalue = None
        block_results = {'last_block': '', 'last_chain': ''}
        blocks_order = [i for i in self.blocks_order]
        if len(blocks_order) == 0:
            blocks_order = ['blocks']

        for chain in blocks_order:
            executed = False
            if chain == 'blocks' and len(self.blocks) > 0:
                executed = True
                last_block, block_results = self.run_blocks(string, state)
                block_results['last_block'] = last_block
                block_results['last_chain'] = chain
            elif chain == 'all' and len(self.all_blocks) > 0:
                executed = True
                last_block, block_results = self.run_all_blocks(string, state)
                block_results['last_block'] = last_block
                block_results['last_chain'] = chain
            elif chain == 'any' and len(self.any_blocks) > 0:
                executed = True
                last_block, block_results = self.run_all_blocks(string, state)
                block_results['last_chain'] = chain
                block_results['last_block'] = last_block
            elif chain == 'none' and len(self.none_blocks) > 0:
                executed = True
                last_block, block_results = self.run_none_blocks(string, state)
                block_results['last_chain'] = chain
                block_results['last_block'] = last_block
            # in each of the check chains here is what the values mean
            # exit tells us we should exit as the result of a failure
            # check is the check we just ran
            # doret is return the value (cresults)
            # extract out last results and use those
            if executed:
                last_block = block_results['last_block']
                block_result = block_results[last_block]
                outcome = block_result.outcome
                doret = block_result.doret
                exit = block_result.exit_on_fail
                rvalue = block_result.block_result
                if doret or exit:
                    break
        if block_results['last_chain'] == '':
            return ChainResult(None, None, False, None, {})
        return ChainResult(chain, block_result, outcome, rvalue, block_results)

    @classmethod
    def from_json(cls, json_data, block_objs={}):
        name = json_data.get('name', None)
        any_blocks = json_data.get('any', [])
        all_blocks = json_data.get('all', [])
        none_blocks = json_data.get('none', [])
        _blocks = any_blocks + all_blocks + none_blocks
        blocks = dict((c, block_objs.get(c)) for c in _blocks
                      if c in block_objs)
        perform_blocks = json_data.get('perform_blocks', [])
        return Chain(name, all_blocks=all_blocks,
                     any_blocks=any_blocks, none_blocks=none_blocks,
                     perform_blocks=perform_blocks, blocks=blocks)
