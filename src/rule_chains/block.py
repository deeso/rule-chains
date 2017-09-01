import json


class BlockResult(object):
    def __init__(self, name, block_fn_result=None, doret=False,
                 exit_on_fail=False, state=None, save_value=None,
                 frontend_results=None, frontend_rule=None,
                 return_value=None, outcome=False):
        self.name = name
        self.block_fn_result = block_fn_result
        self.doret = doret
        self.exit = exit_on_fail
        self.state = state
        self.save_value = save_value
        self.frontend_results = frontend_results
        self.frontend_rule = frontend_rule
        self.return_value = return_value
        self.outcome = outcome

    def get_rule_name(self):
        return self.frontend_rule

    def get_rule_result(self):
        return self.frontend_results


class Block(object):
    STATIC_LIST_LAMBDA = "lambda state, res: all([k in res and res[k] == v" +\
                         " for k, v in state.get('__values', [])])"
    STATIC_DICT_LAMBDA = "lambda state, res: all([k in res and res[k] == v" +\
                         " for k, v in state.get('__values', {{}}).items()])"

    PARAMETERIZED_LAMBDA = "lambda state, res: res is not None and all([])"

    def __init__(self, name, frontend_rule, ctype, cvalue,
                 return_something=False, exit_on_fail=False, 
                 return_rule=None, return_results=False, return_value=None):

        self.frontend = None
        self.name = name
        self.frontend_rule = frontend_rule
        self.ctype = ctype
        self.raw_value = cvalue
        self.set__values = False
        self.__values = None
        self.exit_on_fail = exit_on_fail
        if ctype == 'static_dict':
            self.set__values = True
            self.__values = json.loads(cvalue)

        if ctype == 'static_list':
            self.set__values = True
            self.__values = cvalue

        self.block_fn = self.code_factory(ctype, cvalue)
        self.return_rule = return_rule
        self.return_results = return_results
        self.return_value = None
        self.return_something = return_something or \
            return_rule is not None or \
            return_results

    def update_frontend(self, frontend):
        self.frontend = frontend

    def serialize(self):
        results = {
            'name': self.name,
            'frontend_rule': self.frontend_rule,
            'type': self.ctype,
            'value': self.raw_value,
        }
        if self.exit_on_fail:
            results['exit_on_fail'] = self.exit_on_fail
        if self.return_results:
            results['return_results'] = self.return_results
        elif self.return_rule is not None:
            results['return_rule'] = self.return_rule
        elif self.return_something:
            results['return_value'] = self.return_value
        return results

    @classmethod
    def code_factory(cls, ctype, cvalue):
        if ctype == 'lambda':
            return eval(cvalue)
        elif ctype == 'static_list':
            return eval(cls.STATIC_LIST_LAMBDA)
        elif ctype == 'static_dict':
            return eval(cls.STATIC_DICT_LAMBDA)
        elif ctype == 'function':
            return eval(cvalue)
        return lambda state, res: False

    def execute(self, string, state={}, frontend=None, save_key=None):
        save_value = {}
        state['self'] = self
        br = BlockResult(self.name)
        frontend = frontend if frontend is not None else self.frontend

        if 'frontend' not in state:
            state['frontend'] = frontend

        br.state = state
        if self.set__values:
            state['__values'] = self.__values

        results = frontend.match_pattern(self.frontend_rule, string)
        br.frontend_results = results
        br.frontend_rule = self.frontend_rule

        block_result = None
        if results is not None and len(results) > 0:
            block_result = self.block_fn(state, results)
            # print block_result           

        br.outcome = block_result if isinstance(block_result, bool) \
            else block_result is not None

        br.block_fn_result = block_result
        if save_key is not None:
            save_value = {'grok_results': results,
                          'block_result': block_result}
            state[save_key] = save_value

        del state['self']
        if self.exit_on_fail and not block_result:
            br.exit_on_fail = True
            save_value['exit_on_fail'] = True

        if self.return_results:
            save_value['return'] = True
            save_value['rvalue'] = results
            br.return_value = results
            br.doret = True
            return br
        elif self.return_rule is not None:
            save_value['return'] = True
            save_value['rvalue'] = frontend.match_pattern(self.frontend_rule)
            save_value['return_rule_name'] = self.frontend_rule
            br.return_value = br.frontend_results
            br.doret = True
            br.return_value = save_value['rvalue']
            return br
        elif self.return_value is not None:
            save_value['return'] = True
            save_value['rvalue'] = self.return_value
            br.return_value = self.return_value
            br.doret = True
            return br
        return br

    @classmethod
    def from_json(cls, json_data):
        name = json_data.get('name', None)
        frontend_rule = json_data.get('frontend_rule', None)
        ctype = json_data.get('ctype', None)
        cvalue = json_data.get('cvalue', None)
        if name is None or \
           frontend_rule is None or \
           ctype is None or \
           cvalue is None:
            raise Exception("Missing required Block parameters")

        return_results = json_data.get('return_results', False)
        return_rule = json_data.get('return_rule', False)
        return_value = json_data.get('return_value', None)
        exit_on_fail = json_data.get('exit_on_fail', False)
        return_something = json_data.get('return_something', False)
        return Block(name, frontend_rule, ctype, cvalue,
                     return_something=return_something,
                     return_rule=return_rule,
                     return_results=return_results,
                     return_value=return_value,
                     exit_on_fail=exit_on_fail)
