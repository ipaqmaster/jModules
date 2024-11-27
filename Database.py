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
  def __init__(self, schema, databaseFile=None, backend='sqlite', host='localhost', username='', password='',debug=False):

    self.backend          = backend
    self.databaseBasename = databaseFile.split('.')[0]
    self.host             = host
    self.password         = password
    self.username         = username
    self.schema           = schema
    self.databaseFile     = databaseFile

    self.tables           = []


    # Load a schema from a dict, json file or string of json.
    match schema:
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
          print('schema data is a string but does not appear to be json nor a json file.')
          print("See 'Database.schema.json' for an example.")
          exit(1)

      case _:
        print("Unsure what the provided schema data is.")
        print("See 'Database.schema.json' for an example.")
        exit(1)

    # Determine how many tables we're working with
    for key in self.schema.keys():
      self.tables.append(key)

    if len(self.tables) == 1:
        self.table = self.tables[0]
    
    try: # Configure for the appropriate backend
      if debug: print('Using database backend %s' % self.backend)
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
      print("Failed to establish backend %s: %s" % (self.backend,e))
      exit(1)
    finally:
        if debug: print('Established %s connection' % self.backend)

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
      print('Failed to prepare Database: ', e)
      exit(1)

  def exec(self, query):
    query = query.replace("'None'",'NULL')
    self.cur.execute(query)
    self.con.commit()

  def execFetchAll(self, query):
    self.exec(query)
    return(self.cur.fetchall())

  def execFetchoneDict(self,query):
    self.exec(query)
    row = self.cur.fetchone()
    if row == None:
        return(None)

    rowDict = dict(zip([c[0] for c in self.cur.description], row))
    return(rowDict)


  def insert(self, columns, values, table=None):
    # If no table given and we're only working with a single table, assume that one
    if not table and self.table:
      table = self.table
    else:
      print('Cannot guess table for insert, please provide a table argument.')
      return False

    query = "insert or ignore into %s (%s)" % (table, ', '.join(columns))


    cleanValues = []

    # Escape values, wrap in quotes
    for value in values:
        value = "'%s'" % value.replace("'", "''")
        cleanValues.append(value)

    query += " values (%s)" % ', '.join(cleanValues)

    result = self.exec(query)

    return result
        


