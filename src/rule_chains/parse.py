import toml
from .block import Block
from .chain import Chain
from .chaindef import ChainDefinition
from .dispatch import ChainDispatch

BLOCKS = "blocks"
CHAIN_DEF = "chain_definition"
CHAINS = "chains"
GROUP = "groups"
DISPATCH_TABLES = "chain_tables"


class ParseRuleChainsConfig(object):
    @classmethod
    def parse(cls, toml_config, frontend=None):
        # print toml_config
        data = toml.load(open(toml_config))
        # parse blocks
        blocks_json = data.get(BLOCKS, {})
        block_objs = cls.parse_blocks(blocks_json, frontend=None)
        chains_json = data.get(CHAINS, {})
        chains_objs = cls.parse_chains(chains_json, block_objs=block_objs)
        chain_defs_json_data = data.get(CHAIN_DEF, {})
        chain_defs_objs = cls.parse_chain_definitions(chain_defs_json_data,
                                                      block_objs=block_objs,
                                                      chain_objs=chains_objs)
        groups_data = data.get(GROUP, {})

        dispatch_json_data = data.get(DISPATCH_TABLES)
        cdts = cls.parse_chain_dispatch_tables(dispatch_json_data,
                                               chain_defs_objs,
                                               block_objs)

        if frontend is not None:
            frontend.add_chain_definitions(chain_defs_objs)
            frontend.add_groups(groups_data)
            frontend.add_blocks(block_objs)
            frontend.add_chain_dispatch_tables(cdts)
            frontend.add_chains(chains_objs)

        return {'blocks': block_objs, 'chains': chains_objs,
                'chain_defs': chain_defs_objs, 'groups': groups_data,
                'dispatch_tables': cdts}

    @classmethod
    def parse_groups(cls, groups_json_data, frontend=None):
        groups = {}
        for name, group_json in list(groups_json_data.items()):
            groups[name] = group_json
        return groups

    @classmethod
    def parse_blocks(cls, blocks_json_data, frontend=None):
        blocks_objs = {}
        # print ("Blocks JSON: %s" % blocks_json_data)
        for name, blocks_json in list(blocks_json_data.items()):
            blocks_objs[name] = Block.from_json(blocks_json)
        return blocks_objs

    @classmethod
    def parse_chains(cls, chains_json_data, block_objs={}):
        chains_objs = {}
        # print ("Chains JSON: %s" % chains_json_data)
        for name, chains_json in list(chains_json_data.items()):
            chains_objs[name] = Chain.from_json(chains_json,
                                                block_objs=block_objs)
        return chains_objs

    @classmethod
    def parse_chain_definitions(cls, chain_defs_json_data,
                                chain_objs={}, block_objs={}):
        chain_defs = {}
        # print ("Chain definitions JSON: %s" % chain_defs_json_data)
        for name, chains_json in list(chain_defs_json_data.items()):
            chain_defs[name] = ChainDefinition.from_json(chains_json,
                                                         chain_objs=chain_objs,
                                                         block_objs=block_objs)
        return chain_defs

    @classmethod
    def parse_chain_dispatch_tables(cls, dispatch_json_data,
                                    chain_objs, block_objs):
        chain_dispatch_tables = {}
        # print dispatch_json_data
        for name, dispatch_table_json in list(dispatch_json_data.items()):
            cdt = ChainDispatch.from_json(dispatch_table_json, chains=chain_objs)
            chain_dispatch_tables[name] = cdt
        return chain_dispatch_tables
