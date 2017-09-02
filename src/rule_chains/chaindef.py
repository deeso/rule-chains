class ChainDefinition(object):
    def __init__(self, name, chains_objs={}, chains_order=[]):
        self.name = name
        self.chains_order = chains_order
        self.chains_objs = chains_objs

    def execute_chains(self, string, state={}):
        cr = None
        for cn in self.chains_order:
            if cn not in self.chains_objs:
                m = "Unknown chain name (%s) in %s." % (cn, self.name)
                raise Exception(m)
            chain = self.chains_objs[cn]
            cr = chain.execute_chain(string, state={}, base_save_key='')
            if cr.outcome:
                break
        return cr

    @classmethod
    def from_json(cls, json_data, block_objs={}, chain_objs={}):
        name = json_data.get('name', None)
        chains_order = json_data.get('order', None)
        chains = {}
        chain_names = json_data.get('chains', {})
        for cn in chain_names:
            chain = chain_objs[cn]
            chains[cn] = chain
        return ChainDefinition(name, chains_objs=chains,
                               chains_order=chains_order)
