from typing import Any, Union, List, Set, Dict, Optional, Tuple
from copy import deepcopy

import logging

logger = logging.getLogger('exampleLogger')
logger.setLevel(logging.DEBUG)

class State:
    def __init__(self, data: list|set|dict|int|bytes|float|bool|str|None = {}):
        """
        Initialize a State object with optional initial data.
        
        :param initial_data: Initial collection (list, set, or dict)
        """
        self.data = data

    def _validate_path(self, path: List[str]) -> bool:
        """
        Validate the path for nested access/modification.
        
        :param path: List of nested keys/indices
        :return: Whether the path is valid
        """
        current = self.data
        for key in path[:-1]:
            if isinstance(current, (list, set)):
                try:
                    current = list(current)[int(key)]
                except (ValueError, IndexError):
                    return False
            elif isinstance(current, dict):
                if key not in current:
                    return False
                current = current[key]
            else:
                return False
        return True

    def get(self, *path: int|str|None) -> Any:
        """
        Retrieve a value at the specified nested path.
        
        :param path: List of nested keys/indices
        :return: Value at the specified path
        :raises KeyError: If path is invalid
        """
        print(f"get path: {path}")
        if not self._validate_path(path):
            raise KeyError(f"Invalid path: {path}")

        current = self.data
        for key in path:
            if isinstance(current, (list, set)):
                current = list(current)[int(key)]
            elif isinstance(current, dict):
                current = current[key]
            else:
                return current
        return current

    def add(self, value, *path: str|int|None) -> None:
        """
        Add a value at the specified nested path.
        
        :param path: List of nested keys/indices
        :param value: Value to add
        :raises TypeError: If parent is not a collection
        """
        if not path:
            self.data = value
            return

        current = self.data
        for key in path[:-1]:
            if isinstance(current, list):
                idx = int(key)
                while len(current) <= idx:
                    current.append(None)
                current = current[idx]
            elif isinstance(current, dict):
                if key not in current:
                    current[key] = {}
                current = current[key]
            elif isinstance(current, set):
                current = list(current)[int(key)]
            else:
                raise TypeError(f"Cannot add to non-collection type at {key}")

        last_key = path[-1]
        if isinstance(current, list):
            idx = int(last_key)
            while len(current) <= idx:
                current.append(None)
            current[idx] = value
        elif isinstance(current, dict):
            current[last_key] = value
        elif isinstance(current, set):
            current_list = list(current)
            current_list[int(last_key)] = value
            current = set(current_list)
        else:
            raise TypeError("Cannot add to non-collection type")

    def remove(self, path: List[str]) -> None:
        """
        Remove a value at the specified nested path.
        
        :param path: List of nested keys/indices
        :raises KeyError: If path is invalid
        """
        if not path:
            self.data = {}
            return

        current = self.data
        for key in path[:-1]:
            if isinstance(current, (list, set)):
                current = list(current)[int(key)]
            elif isinstance(current, dict):
                current = current[key]
            else:
                raise KeyError(f"Cannot remove from non-collection type at {key}")

        last_key = path[-1]
        if isinstance(current, list):
            del current[int(last_key)]
        elif isinstance(current, dict):
            del current[last_key]
        elif isinstance(current, set):
            current_list = list(current)
            del current_list[int(last_key)]
            current = set(current_list)
        else:
            raise TypeError("Cannot remove from non-collection type")

    def insert(self, value: Any, *path: str|int|None) -> None:
        """
        Insert a value at a specific position in a list.
        
        :param path: List of nested keys/indices
        :param value: Value to insert
        :param index: Optional index for insertion (defaults to end)
        :raises TypeError: If parent is not a list
        """
        if not path:
            raise TypeError("Cannot insert into root")

        current = self.data
        for key in path[:-1]:
            if isinstance(current, (list, set)):
                current = list(current)[int(key)]
            elif isinstance(current, dict):
                current = current[key]
            else:
                raise TypeError(f"Cannot insert into non-list type at {key}")

        last_key = path[-1]
        if isinstance(current, list):
            if index is None:
                current.append(value)
            else:
                current.insert(int(index), value)
        else:
            raise TypeError("Can only insert into lists")

    def copy(self) -> 'State':
        """
        Create a deep copy of the State object.
        
        :return: New State object with deep copied data
        """
        return State(deepcopy(self.data))

    def __repr__(self) -> str:
        """
        String representation of the State object.
        
        :return: String representation of internal data
        """
        return f"State({repr(self.data)})"

import unittest

class StateTestRootValuee(unittest.TestCase):
    def test_primitive_values(self):
        state = State(1)
        self.assertEqual(state.get(), 1)
        state = State(1.3)
        self.assertEqual(state.get(), 1.3)
        state = State("hello")
        self.assertEqual(state.get(), "hello")

    def test_dictionary(self):
        state = State({"key": 5})
        self.assertEqual(state.get(), {"key": 5})

    def test_set(self):
        state = State({1,2,3})
        self.assertEqual(state.get(), {1,2,3})
        self.assertIsInstance(state.get(), set)
    
        

class StateTestFirstLevelValues(unittest.TestCase):
    def test_dictionary_values(self):
        state = State({
            "key1": 1,
            "key2": 2
        })
        self.assertEqual(state.get("key1"), 1)
        self.assertEqual(state.get("key2"), 2)

    def test_list_values(self):
        state = State([1,2])
        self.assertEqual(state.get(0), 1)
        self.assertEqual(state.get(1), 2)


class StateTestNestedLeafValues(unittest.TestCase):
    def test_dict_of_values(self):
        state = State({
            'some_text': "hello",
            "a_number": 5
        })
        self.assertEqual(state.get("some_text"), "hello")
        self.assertEqual(state.get("a_number"), 5)

    def test_list_of_values(self):
        state = State([1, "second_item", True])
        self.assertEqual(state.get(0), 1)
        self.assertEqual(state.get(1), "second_item")
        self.assertEqual(state.get(2), True)

    def test_dict_of_dict(self):
        state = State({
            'text': "hello",
            'obj1': {
                'attr1': "VALUE1",
                'attr2': "VALUE2"
            },
            'obj2': {
                'attr1': "VALUE3",
                'attr2': "VALUE4"
            }
        })
        self.assertEqual(state.get("text"), "hello")
        self.assertEqual(state.get("obj1", "attr1"), "VALUE1")
        self.assertEqual(state.get("obj1", "attr2"), "VALUE2")
        self.assertEqual(state.get("obj2", "attr1"), "VALUE3")
        self.assertEqual(state.get("obj2", "attr2"), "VALUE4")

    def test_list_of_dicts(self):
        state = State([
            {'name': 'Mása'},
            {'name': 'Judit'},
        ])
        self.assertEqual(state.get(0, 'name'), "Mása")
        self.assertEqual(state.get(1, 'name'), "Judit")

    def test_compositions(self):
        state = State([
            'definitions' """# this is a python script""",
            'graph':{
                'nodes':[
                    {
                        'name': "read_text",
                        'func': "Path.read_text"
                    },
                    {
                        'name': "node1",
                        'func': "print"
                    }
                ],
                'links':[
                    {
                        'source': "node1",
                        'target': "print",
                        'inlet': "text"
                    },
                    {
                        'name': "node1",
                        'func': "print"
                    }
                ],
            }
        ])
        self.assertEqual(state.get(0, 'name'), "Mása")
        self.assertEqual(state.get(1, 'name'), "Judit")

    



if __name__ == "__main__":
    state = State()
    unittest.main()
    # state.add([], {})  # Initialize the root with a dictionary
    # state.add(["users"], [])  # Add a list under the key 'users'
    # state.add(["users"], {"id": 1, "name": "Alice"})  # Add a dict to the 'users' list
    # state.insert(["users"], {"id": 2, "name": "Bob"}, index=1)  # Insert another dict
    # state.remove(["users", 0])  # Remove the first user

    # print(state.get(["users", 0]))  # Access the first user after removal
    # print(state)