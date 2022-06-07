import ast
import json

from project import parse_ast
from parse import parse_file
from code_to_readable import PARSED_SNIPPETS


class AutoComplete():
    def __init__(self):
        self.table = {}
        self.lines = ""
        self.value2types = {}
        self.types2values = {}
        self.namespaces = {}

    # CREATES A LOCAL COLLECTION TO LEARN FROM
    def log_values(self, base, curr_val):
        if 'children' in base and 'value' in base:
            for child in base['children']:
                if 'value' in child:
                    if base['value'] in self.namespaces:
                        self.namespaces[base['value']].append(child['value'])
                    else:
                        self.namespaces[base['value']] = [child['value']]

    def create_chain(self, base, coll, indexed=True):
        if 'children' in base:
            for child in base['children']:
                # self.table[base['type'], coll[children]['type']] = self.table.get(
                #     (base['type'], coll[children]['type']), 0) + 1
                if indexed:
                    child_item = coll[child]
                else:
                    child_item = child
                if base['type'] in self.table:
                    if coll[child]['type'] in self.table[base['type']]:
                        self.table[base['type']][child_item['type']] += 1
                    else:
                        self.table[base['type']][child_item['type']] = 1
                else:
                    self.table[base['type']] = {
                        child_item['type']: 1
                    }

                self.create_chain(child_item, coll)

    def get_percentages(self):
        percent_tables = {}

        for item, val in self.table.items():
            total = sum(map(lambda x: x[1], val.items()))
            percentages = {k: v/total for k, v in val.items()}
            percent_tables[item] = percentages

        return percent_tables

    def train(self, file):
        f = open(file)
        lines = f.readlines()

        for coll in lines[:1000]:
            item = json.loads(coll)
            self.create_chain(item[0], item)

    def generate_types_values(self, tree):
        tree = json.loads(tree)

        for item in tree:
            self.value2types['value'] = item['type']

            if self.value2types['value'] not in self.types2values['type']:
                self.types2values['value'].append(self.value2types['value'])

    def generate_ast(self):
        tree = None

        tree = parse_file(self.lines)

        return tree
        # self.generate_types_values(tree)

    def get_top(self, key):
        if key in self.table:
            return list(map(lambda x: x if x[0] not in PARSED_SNIPPETS else PARSED_SNIPPETS[x[0]], sorted(self.table[key].items(), key=lambda x: x[1],  reverse=True)))

    @staticmethod
    def parse_func_call(text):
        if text[-1] == "(":
            return text.replace("(", ""), 'Call'
        elif text[-1] == ".":
            return text.replace(".", ""), "AttributeLoad"
        elif text[-1] == "=":
            return text.replace("=", ""), "Assign"

        return text, None

    def listen(self):
        print("Suggestions: ", self.get_top('Module'))
        while True:
            input_var = input()
            parsed, key = self.parse_func_call(input_var)

            self.lines += parsed + "\n"

            if (input_var[-1] != " "):
                last = {'type': key}

                if not key:
                    tree = self.generate_ast()
                    last = json.loads(tree)[-1]

                print('Current type: ',
                      last['type'], " Suggestions: ", self.get_top(last['type']))


a = AutoComplete()

a.train("data/python50k_eval.json")
print('Training finished')

a.listen()
