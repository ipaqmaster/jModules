#!/usr/bin/env python
import hashlib
import json
import re
import time
import datetime
import os
from dateutil import parser

#Usage:
# Refer to Database.schema.json for an example schema to pass in.
#   from jModules.Database import Database
#   database = Database(databaseFile=dbFile, schema=schemaFile)

class Database: # Our database object
  def __init__(self, schema=None, databaseFile=None, backend='sqlite', host='localhost', username='', password='', debug=False):

    self.backend          = backend
    self.databaseBasename = databaseFile.split('.')[0]
    self.debug            = debug
    self.host             = host
    self.password         = password
    self.username         = username
    self.schema           = schema
    self.databaseFile     = databaseFile

    self.tables           = []
    self.table            = None

    try: # Configure for the appropriate backend
      if self.debug:
          print(f'[{__name__}] Using database backend %s' % self.backend)

      match self.backend:
        case 'sqlite':
          import sqlite3
          if not databaseFile.endswith('.sqlite') and not databaseFile.endswith('.db'):
            self.databaseFile = databaseFile + '.db'

          self.con = sqlite3.connect(self.databaseFile,check_same_thread=False)
          self.cur = self.con.cursor()

        case 'mysql':
          import MySQLdb
          if not self.username:
              self.username = self.databaseBasename

          self.con = MySQLdb.connect(host=self.host,
                                     user=self.username,
                                     password=self.password,
                                     database=self.databaseBasename,connect_timeout=5)
          self.cur = self.con.cursor()

    except Exception as e:
      print(f"[{__name__}] Failed to establish backend %s: %s" % (self.backend,e))
      exit(1)
    finally:
        if self.debug: print(f'[{__name__}] Established %s connection' % self.backend)

    if self.schema: # If provided load a schema from a dict, json file or json string.
        match self.schema:
          case dict():
            # Read a dict in directly
            self.schema = schema

          case str():
            # Try loading a file
            if os.path.isfile(schema):
              with open(schema, 'r') as file:
                self.schema = json.load(file)

            elif jsonString.startswith('{'):
              # Try loading the string
              self.schema = json.load(schema)

            else:
              print(f'[{__name__}] schema data is a string but does not appear to be json nor a json file.')
              print(f"[{__name__}] See 'Database.schema.json' for an example.")
              exit(1)

          case _:
            print(f"[{__name__}] Unsure what the provided schema data is.")
            print(f"[{__name__}] See 'Database.schema.json' for an example.")
            exit(1)

        # Determine how many tables we're working with
        for key in self.schema.keys():
          self.tables.append(key)

        if len(self.tables) == 1:
            self.table = self.tables[0]



        try: # Create our database and tables

          for table in list(self.schema.keys()): # Build the database
            tableQuery = "create table if not exists %s" %(table)

            columnCount = len(self.schema[table]['columns'])
            counter = 1

            columnQuery = ''


            for column in self.schema[table]['columns'].keys():
              columnQuery += column + ' ' + self.schema[table]['columns'][column]['type']

              # Check for any special column features and add them
              if 'typeSpecial' in self.schema[table]['columns'][column]:
                if self.backend in self.schema[table]['columns'][column]['typeSpecial']:
                  columnQuery += " %s" % self.schema[table]['columns'][column]['typeSpecial'][self.backend]

              if counter < 2:
                columnQuery = ' ' + columnQuery
              if counter < columnCount:
                columnQuery += ', '
              else:
                columnQuery += ' '

              counter += 1

            if 'columnSpecial' in self.schema[table]:
              if self.schema[table]['columnSpecial'][self.backend]:
                columnQuery += ', %s' % self.schema[table]['columnSpecial'][self.backend]

            tableQuery += ' (' + columnQuery + ')'

            if 'tableSpecial' in self.schema[table]:
              if self.schema[table]['tableSpecial'][self.backend]:
                tableQuery += ' %s' % self.schema[table]['tableSpecial'][self.backend]

            self.exec(tableQuery)

        except Exception as e:
          print(f'[{__name__}] Failed to prepare Database: ', e)
          exit(1)

  def exec(self, query):
    if self.debug:
        t1 = time.time()

    query = query.replace("'None'",'NULL')
    self.cur.execute(query)
    self.con.commit()

    if self.debug:
        t2 = time.time()
        print(f'[{__name__}] Query took: {t2 - t1}')

  def execFetchAll(self, query):
    self.exec(query)
    return(self.cur.fetchall())

  def execFetchone(self,query):
    self.exec(query)
    return(self.cur.fetchone())

  def execFetchAllDict(self, query, showEmpty=False):
    self.exec(query)
    rows = self.cur.fetchall()
    results = []

    if rows == None:
        if not showEmpty:
            return(None)
    else:
        desc = self.cur.description
        for row in rows:
            results.append(dict(zip([c[0] for c in desc], row)))

    return(results)

  def execFetchoneDict(self,query, showEmpty=False):
    self.exec(query)
    row = self.cur.fetchone()

    if row == None:
        if not showEmpty:
            return(None)
        else:
            row = []
            for column in self.cur.description:
                row.append(None)

    return(dict(zip([c[0] for c in self.cur.description], row)))


  def query(self, columns, values, mode='insert ignore into', order_by_column=None, order_by_desc=False, table=None, where=None, Dict=False, fetch_all=False, limit=None):
    # If no table given and we're only working with a single table, assume that one
    if not table and self.table:
      table = self.table
    elif not table:
      print(f'[{__name__}] Cannot guess table for insert, please provide a table argument.')
      return False

    query = "%s %s" % (mode, table)



    if 'insert' in mode:
        query += " (%s)" % ', '.join(columns)
        cleanValues = []

        # Escape values, run through escape_string
        for value in values:
            value = "'%s'" % self.con.escape_string(value).decode("utf-8")
            cleanValues.append(value)

        query += " values (%s)" % ', '.join(cleanValues)

    elif 'update' in mode:
        query += " set "
        preparedSets = []
        for i in range(0, len(columns)):
            preparedSets.append("%s = '%s'" % (columns[i], values[i]))

        query += ', '.join(preparedSets)


    if where: # Accept multiple where (x == y) tuples in a list.
        wheres = []
        for clause in where:
            wheres.append("%s %s '%s'" % (clause[0], clause[1], self.con.escape_string(clause[2]).decode("utf-8")))

        query += ' where ' + ' and '.join(wheres)


    if order_by_column:
        query += " order by %s" % order_by_column
        if order_by_desc:
            query += " desc"

    if limit and type(limit) == int:
        query += f" limit {limit}"

    if self.debug:
        print(f'[{__name__}] Raw query:')
        print(f'[{__name__}] {query}')

    # Run queries below this line
    if 'select' in mode:
        if fetch_all:
            if Dict:
                result = self.execFetchAllDict(query)
            else:
                result = self.execFetchAll(query)
        else:
            if Dict:
                result = self.execFetchoneDict(query)
            else:
                result = self.execFetchone(query)

    else:
        result = self.exec(query)

    return(result)




