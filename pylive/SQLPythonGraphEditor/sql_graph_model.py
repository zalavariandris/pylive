from typing import *
from PySide6.QtCore import *
from PySide6.QtSql import *

from itertools import chain

class MyClass:
    def __init__(self):
        self.name:str


class MySqlRelationalTableModel(QSqlRelationalTableModel):
    def flags(self, index):
        if index.column() == self.fieldIndex("key"):  # Replace "key" with your column name
            return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        return super().flags(index)

class SQLGraphModel(QObject):
    def __init__(self, parent:QObject|None=None):
        super().__init__(parent=parent)
        self.db:QSqlDatabase
        self.graphs:QSqlRelationalTableModel
        self.nodes:QSqlRelationalTableModel
        self.edges:QSqlRelationalTableModel

        ### setup sql database
        self._create_database()
        self._populate_database()
        self._create_models()

    def _create_database(self):
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(":memory:")

        if not self.db.open():
            print("Error: Cannot open database")
            return False

        queries = []

        queries.append("""CREATE TABLE graph (
            key INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT
        )""")
        
        queries.append("""CREATE TABLE node (
            key INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT, 
            graph INTEGER, 
            FOREIGN KEY(graph) REFERENCES graph(key))
        """)

        queries.append("""CREATE TABLE edge (
            key INTEGER PRIMARY KEY AUTOINCREMENT, 
            source_node INTEGER, 
            target_node INTEGER, 
            FOREIGN KEY(source_node) REFERENCES node(key),
            FOREIGN KEY(target_node) REFERENCES node(key)
        )""")

        query = QSqlQuery(self.db)
        for create_query in queries:
            if not query.exec(create_query):
                print(f"Error creating tables: {query.lastError().text()}")

    def _create_models(self):
        # graphs table
        self.graphs = QSqlRelationalTableModel(self, self.db)
        self.graphs.setTable("graph")
        self.graphs.select()

        ### nodes table
        self.nodes = QSqlRelationalTableModel(self, self.db)
        self.nodes.setTable("node")
        self.nodes.setRelation(2, QSqlRelation("graph", "key", "name"))
        self.nodes.select()
        self.nodes.setHeaderData(1, Qt.Orientation.Horizontal, "name")
        self.nodes.setHeaderData(2, Qt.Orientation.Horizontal, "graph")

        ### edges table
        self.edges = QSqlRelationalTableModel(self, self.db)

        self.edges.setTable("edge")
        self.edges.setRelation(1, QSqlRelation("node", "key", "name"))
        self.edges.setRelation(2, QSqlRelation("node", "key", "name"))
        self.edges.setHeaderData(1, Qt.Orientation.Horizontal, "source")
        self.edges.setHeaderData(2, Qt.Orientation.Horizontal, "target")
        self.edges.select()

    def _populate_database(self):
        ### create initial data
        graph_inserts = [
            "INSERT INTO graph (name) VALUES ('MainGraph')"
        ]
        node_inserts = [
            "INSERT INTO node (graph, name) VALUES (1, 'NodeA')",
            "INSERT INTO node (graph, name) VALUES (1, 'NodeB')",
            "INSERT INTO node (graph, name) VALUES (1, 'NodeC')"
        ]
        edge_inserts = [
            "INSERT INTO edge (source_node, target_node) VALUES (1, 2)",
            "INSERT INTO edge (source_node, target_node) VALUES (2, 3)",
            "INSERT INTO edge (source_node, target_node) VALUES (3, 1)"
        ]

        query = QSqlQuery(self.db)
        for insertion in chain(graph_inserts, node_inserts, edge_inserts):
            if not query.exec(insertion):
                print(f"Error creating tables: {query.lastError().text()}")

    def add_graph(self, graph_name: str) -> int:
        assert self.graphs
        """Add a new graph to the database."""
        row = self.graphs.rowCount()
        self.graphs.insertRow(row)
        self.graphs.setData(self.graphs.index(row, 1), graph_name)  # Set the name of the graph

        if self.graphs.submitAll():  # Save to the database
            return self.graphs.record(row).value("key")  # Return the key (ID) of the new graph
        else:
            print(f"Error adding graph: {self.graphs.lastError().text()}")
            return -1

    def remove_graph(self, graph_key: int) -> bool:
        assert self.graphs
        """Remove a graph and its associated nodes and edges."""
        # Find the row corresponding to the graph_key
        row = -1
        for i in range(self.graphs.rowCount()):
            if self.graphs.record(i).value("key") == graph_key:
                row = i
                break

        if row == -1:
            print("Graph not found.")
            return False

        # Delete associated edges (via nodes)
        self.db.transaction()
        try:
            # Remove edges associated with this graph's nodes
            query = QSqlQuery(self.db)
            query.prepare("DELETE FROM edge WHERE source_node IN (SELECT key FROM node WHERE graph = :graph_key) OR target_node IN (SELECT key FROM node WHERE graph = :graph_key)")
            query.bindValue(":graph_key", graph_key)
            if not query.exec():
                raise Exception(f"Error deleting edges: {query.lastError().text()}")

            # Remove nodes for this graph
            query.prepare("DELETE FROM node WHERE graph = :graph_key")
            query.bindValue(":graph_key", graph_key)
            if not query.exec():
                raise Exception(f"Error deleting nodes: {query.lastError().text()}")

            # Remove the graph itself
            self.graphs.removeRow(row)
            if not self.graphs.submitAll():
                raise Exception(f"Error removing graph: {self.graphs.lastError().text()}")

            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(e)
            return False

    def add_node(self, graph_key: int, node_name: str) -> int:
        assert self.nodes
        """Add a node to a specific graph."""
        row = self.nodes.rowCount()
        self.nodes.insertRow(row)
        self.nodes.setData(self.nodes.index(row, 1), node_name)  # Set the node name
        self.nodes.setData(self.nodes.index(row, 2), graph_key)  # Set the graph ID

        if self.nodes.submitAll():  # Save to the database
            return self.nodes.record(row).value("key")  # Return the node's key (ID)
        else:
            print(f"Error adding node: {self.nodes.lastError().text()}")
            return -1

    def remove_node(self, node_key: int) -> bool:
        assert self.nodes
        """Remove a node and its associated edges."""
        row = -1
        for i in range(self.nodes.rowCount()):
            if self.nodes.record(i).value("key") == node_key:
                row = i
                break

        if row == -1:
            print("Node not found.")
            return False

        # Delete associated edges
        self.db.transaction()
        try:
            # Remove edges associated with this node
            query = QSqlQuery(self.db)
            query.prepare("DELETE FROM edge WHERE source_node = :node_key OR target_node = :node_key")
            query.bindValue(":node_key", node_key)
            if not query.exec():
                raise Exception(f"Error deleting edges: {query.lastError().text()}")

            # Remove the node itself
            self.nodes.removeRow(row)
            if not self.nodes.submitAll():
                raise Exception(f"Error removing node: {self.nodes.lastError().text()}")

            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(e)
            return False

    def add_edge(self, source_node_key: int, target_node_key: int) -> int:
        assert self.edges
        """Add an edge between two nodes."""
        row = self.edges.rowCount()
        self.edges.insertRow(row)
        self.edges.setData(self.edges.index(row, 1), source_node_key)
        self.edges.setData(self.edges.index(row, 2), target_node_key)

        if self.edges.submitAll():  # Save to the database
            return self.edges.record(row).value("key")  # Return the edge's key (ID)
        else:
            print(f"Error adding edge: {self.edges.lastError().text()}")
            return -1

    def remove_edge(self, edge_key: int) -> bool:
        assert self.edges
        """Remove an edge."""
        row = -1
        for i in range(self.edges.rowCount()):
            if self.edges.record(i).value("key") == edge_key:
                row = i
                break

        if row == -1:
            print("Edge not found.")
            return False

        self.edges.removeRow(row)
        if not self.edges.submitAll():  # Save to the database
            print(f"Error removing edge: {self.edges.lastError().text()}")
            return False
        return True
