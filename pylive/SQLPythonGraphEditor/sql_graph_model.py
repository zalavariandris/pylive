#sql_graph_model.py

from typing import *
from PySide6.QtCore import *
from PySide6.QtSql import *

from itertools import chain

from PySide6.QtWidgets import QApplication


# class MySqlRelationalTableModel(QSqlRelationalTableModel):
#     def flags(self, index):
#         if index.column() == self.fieldIndex("key"):  # Replace "key" with your column name
#             return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
#         return super().flags(index)

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
        self.nodes.setHeaderData(1, Qt.Orientation.Horizontal, "name")
        self.nodes.setHeaderData(2, Qt.Orientation.Horizontal, "graph")
        
        self.nodes.select()
        

        ### edges table
        self.edges = QSqlRelationalTableModel(self, self.db)

        self.edges.setTable("edge")
        self.edges.setRelation(1, QSqlRelation("node", "key", "name"))
        self.edges.setRelation(2, QSqlRelation("node", "key", "name"))
        self.edges.setHeaderData(1, Qt.Orientation.Horizontal, "source")
        self.edges.setHeaderData(2, Qt.Orientation.Horizontal, "target")

        self.edges.select()

        self.graphs.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        self.nodes.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        self.edges.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)

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

    def create_graph(self, name: str) -> int:
        """
        Create a new graph and return its key.
        
        Args:
            name (str): Name of the graph
        
        Returns:
            int: Key of the newly created graph
        """
        row = self.graphs.rowCount()
        self.graphs.beginInsertRows(QModelIndex(), row, row)
        record = self.graphs.record()
        record.setValue("name", name)
        self.graphs.insertRecord(-1, record)
        self.graphs.endInsertRows()
        self.graphs.submitAll()
        
        # Return the key of the last inserted graph
        return self.graphs.record(row).value("key")

    def delete_graph(self, graph_key: int):
        """
        Delete a graph and all its associated nodes and edges.
        
        Args:
            graph_key (int): Key of the graph to delete
        """
        # Delete associated edges first
        edge_filter = f"source_node IN (SELECT key FROM node WHERE graph = {graph_key}) OR " \
                      f"target_node IN (SELECT key FROM node WHERE graph = {graph_key})"
        self.edges.setFilter(edge_filter)
        while self.edges.rowCount() > 0:
            self.edges.removeRow(0)
        self.edges.setFilter("")
        
        # Delete nodes of the graph
        self.nodes.setFilter(f"graph = {graph_key}")
        while self.nodes.rowCount() > 0:
            self.nodes.removeRow(0)
        self.nodes.setFilter("")
        
        # Delete the graph itself
        for row in range(self.graphs.rowCount()):
            if self.graphs.record(row).value("key") == graph_key:
                self.graphs.beginRemoveRows(QModelIndex(), row, row)
                self.graphs.removeRow(row)
                self.graphs.endRemoveRows()
                break

    def add_node(self, graph_key: int, name: str) -> int:
        """
        Add a node to a specific graph.
        
        Args:
            graph_key (int): Key of the graph to add the node to
            name (str): Name of the node
        
        Returns:
            int: Key of the newly created node
        """
        print(f"!!!!!add_node, graph_key: {graph_key}, name:{name}")
        row = self.nodes.rowCount()

        # Begin inserting the row
        self.nodes.beginInsertRows(QModelIndex(), row, row)
        
        # Create a new record and set its values
        record = self.nodes.record()
        record.setValue("name", name)
        record.setValue("graph", graph_key)
        
        # Insert the record into the model
        if not self.nodes.insertRecord(row, record):
            print("cant insert record")
        
        # End inserting rows
        self.nodes.endInsertRows()

        # Commit changes to the database
        if not self.nodes.submitAll():
            print("Error submitting data:")
            print("-", self.nodes.lastError().text())

        # Get the key of the newly inserted node
        new_node_key =  self.nodes.record(row).value("key")
        print(new_node_key)
        return new_node_key


    def delete_node(self, node_key: int):
        """
        Delete a node and all its associated edges.
        
        Args:
            node_key (int): Key of the node to delete
        """
        # First, delete associated edges
        self.edges.setFilter(f"source_node = {node_key} OR target_node = {node_key}")
        while self.edges.rowCount() > 0:
            self.edges.removeRow(0)
        self.edges.setFilter("")  # Clear the filter after removing rows
        
        # Now, delete the node itself
        self.nodes.setFilter(f"key = {node_key}")
        for row in range(self.nodes.rowCount()):
            self.nodes.beginRemoveRows(QModelIndex(), row, row)
            self.nodes.removeRow(row)
            self.nodes.endRemoveRows()
        self.nodes.setFilter("")  # Clear the filter after removing rows

    def add_edge(self, source_node_key: int, target_node_key: int) -> int:
        """
        Add an edge between two nodes.
        
        Args:
            source_node_key (int): Key of the source node
            target_node_key (int): Key of the target node
        
        Returns:
            int: Key of the newly created edge
        """
        row = self.edges.rowCount()
        self.edges.beginInsertRows(QModelIndex(), row, row)
        record = self.edges.record()
        record.setValue("source_node", source_node_key)
        record.setValue("target_node", target_node_key)
        self.edges.insertRecord(-1, record)
        self.edges.endInsertRows()
        
        # Return the key of the last inserted edge
        return self.edges.record(row).value("key")

    def delete_edge(self, edge_key: int):
        """
        Delete a specific edge.
        
        Args:
            edge_key (int): Key of the edge to delete
        """
        for row in range(self.edges.rowCount()):
            if self.edges.record(row).value("key") == edge_key:
                self.edges.beginRemoveRows(QModelIndex(), row, row)
                self.edges.removeRow(row)
                self.edges.endRemoveRows()
                break

        self.edges.submitAll()


if __name__ == "__main__":
    app = QApplication()
    model = SQLGraphModel()


    app.exec()