import json


class BlockResult(object):
    def __init__(self, name, block_fn_result=None, doret=False,
                 exit_on_fail=False, state=None, save_value=None,
                 frontend_results=None, frontend_rule=None,
                 return_value=None, outcome=False, return_rule=None):
        self.block_name = name
        self.block_fn_result = block_fn_result
        self.doret = doret
        self.exit = exit_on_fail
        self.state = state
        self.save_value = save_value
        self.frontend_rule = frontend_rule
        self.frontend_results = frontend_results
        self.return_rule = return_rule
        self.return_value = return_value
        self.outcome = outcome
        # print self.block_name, self.return_rule

    def get_rule_name(self):
        if self.return_rule is not None:
            return self.return_rule
        return self.frontend_rule

    def get_rule_result(self):
        if self.return_rule is not None:
            return self.return_value
        return self.frontend_results


class Block(object):
    CO_CREATE_FAILED = "Code object (%s) from: %s not created"
    CO_MISSING = "Code object for: %s not in globals or locals"
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
        cf_name = self.name + "_" + ctype
        self.block_fn = self.code_factory(ctype, cvalue, cf_name)
        self.return_rule = return_rule
        self.return_results = return_results
        self.return_value = None
        self.return_something = return_something or \
            return_rule is not None or \
            return_results

        # print self.name, self.return_rule

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
    def code_factory(cls, ctype, cvalue, cf_name):
        if ctype == 'lambda':
            return eval(cvalue)
        elif ctype == 'static_list':
            return eval(cls.STATIC_LIST_LAMBDA)
        elif ctype == 'static_dict':
            return eval(cls.STATIC_DICT_LAMBDA)
        elif ctype == 'function':
            co = None
            fn_obj = None
            # compile script to usable code
            try:
                co = compile(cvalue, '<string>', 'exec')
            except Exception as e:
                raise Exception(cls.CO_CREATE_FAILED % (cf_name, str(e)))

            # eval the code to get it in the environment
            if co is not None:
                eval(co)

            # find the function in the globals or locals
            fn_obj = globals().get(cf_name, None)
            if fn_obj is None:
                fn_obj = locals().get(cf_name, None)

            if fn_obj is None:
                raise Exception(cls.CO_MISSING % cf_name)
            return fn_obj
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

        initial_results = frontend.match_pattern(self.frontend_rule, string)
        br.frontend_results = initial_results
        br.frontend_rule = self.frontend_rule

        block_fn_result = None
        _rule_results = initial_results.get('rule_results', {})
        if _rule_results is not None and len(_rule_results) > 0:
            block_fn_result = self.block_fn(state, _rule_results)
            # print block_fn_result
        br.outcome = block_fn_result if isinstance(block_fn_result, bool) \
            else block_fn_result is not None

        br.block_fn_result = block_fn_result
        if save_key is not None:
            save_value = {'grok_results': initial_results,
                          'block_fn_result': block_fn_result}
            state[save_key] = save_value

        del state['self']
        if self.exit_on_fail and not block_fn_result:
            br.exit_on_fail = True
            save_value['exit_on_fail'] = True

        if block_fn_result and self.return_results and\
                self.return_rule is not None:

            save_value['return'] = True
            rresults = frontend.match_pattern(self.return_rule, string)
            br.return_value = rresults
            br.return_rule = self.return_rule
            save_value['rvalue'] = rresults
            save_value['return_rule_name'] = self.return_rule
            # br.return_value = br.frontend_results
            br.doret = True
            return br
        elif block_fn_result and self.return_results and\
                self.return_rule is None:

            save_value['return'] = True
            save_value['rvalue'] = initial_results
            br.return_value = initial_results
            br.doret = True
            return br
        elif block_fn_result and self.return_value is not None:
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
        return_rule = json_data.get('return_rule', None)
        return_value = json_data.get('return_value', None)
        exit_on_fail = json_data.get('exit_on_fail', False)
        return_something = json_data.get('return_something', False)
        return Block(name, frontend_rule, ctype, cvalue,
                     return_something=return_something,
                     return_rule=return_rule,
                     return_results=return_results,
                     return_value=return_value,
                     exit_on_fail=exit_on_fail)
