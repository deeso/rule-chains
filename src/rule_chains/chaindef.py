class ChainDefinition(object):
    def __init__(self, name, chains=[], chain_objs={}, chains_order=[]):
        self.name = name
        self.chains = chains
        self.chains_order = chains_order
        self.chain_objs = chains

    @classmethod
    def from_json(cls, json_data, block_objs={}, chain_objs={}):
        name = json_data.get('name', None)
        chains_order = json_data.get('chains_order', None)
        chains = {}
        json_chains = json_data.get('chains', {})
        for name, _chain in json_chains.items():
            chain = chain_objs[name]
            chains[name] = chain
        return ChainDefinition(name, chains=chains,
                               chains_order=chains_order)
