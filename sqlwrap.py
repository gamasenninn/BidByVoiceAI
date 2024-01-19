#import sqlite3
import os
import pyodbc
import json
from datetime import datetime,date
from decimal import Decimal
#from decimal import decimal
import MySQLdb
from dotenv import load_dotenv


load_dotenv()

white_list =[
    {'table_name':'商品マスタ2','select':True,'insert':True,'update':True,'delete':True},
    {'table_name':'出品商品管理票','select':True,'insert':True,'update':False,'delete':False},
]

def is_table_and_op_allowed(table_name, operation):
    for entry in white_list:
        if entry['table_name'] == table_name:
            return entry.get(operation, False)
    return False

def sqlify_for_insert(string_iterable):
    return f'({",".join(string_iterable)})'

def sqlify_for_update(string_iterable):
    return f'{"=?,".join(string_iterable)+"=?"}'

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def support_datetime_default(o):
    if isinstance(o, (datetime,date)):
        return o.isoformat()
    if isinstance(o, Decimal):
        return int(o)
    raise TypeError(repr(o) + " is not JSON serializable")

#----- Insert operation

def dict_insert(conn, table_name, d):
    if not is_table_and_op_allowed(table_name, 'insert'):
        return f"ERROR: Insert operation is not allowed on table '{table_name}'."

    try:
        pre_vals = tuple(d.values())
        sql = 'insert into {table_name} {keys} values {replacement_fields}'.format(
                table_name=table_name,
                keys=sqlify_for_insert(d), 
                #replacement_fields=sqlify_for_insert('?'*len(d)).replace('?','%s') 
                replacement_fields=sqlify_for_insert('?'*len(d)) 
            )
        ret = conn.execute( sql, pre_vals )
        return "OK: "+"{sql} {values}".format(sql=sql,values=pre_vals)
    except Exception as e:
        return f"SQL ERROR: {e}\n"+ "{sql} {values}".format(sql=sql,values=pre_vals)

def json_insert(conn,table_name,j):
    dic_d = json.loads(j)
    return dict_insert(conn,table_name,dic_d)

#------ Update operation

def dict_update(conn,table_name,d,key_name):
    if not is_table_and_op_allowed(table_name, 'update'):
        return f"ERROR: Update is not allowed on table '{table_name}'."
    
    v = d.pop(key_name)
    vl=[v]

    try:
        pre_vals = tuple(d.values())+tuple(vl)
        sql ='update {table_name} set {key_values} where {key_name} = ? '.format(
                table_name=table_name,
                key_values=sqlify_for_update(d),
                key_name = key_name
            )
        c = conn.cursor()
        c.execute( sql, pre_vals )
        return "OK: "+"{sql} {values}".format(sql=sql,values=pre_vals)
    except:
        return "SQL ERROR" +"{sql} {values}".format(sql=sql,values=pre_vals)

def json_update(conn,table_name,j,key_name):
    dic_j = json.loads(j)
    return dict_update(conn,table_name,dic_j,key_name)

#------Upsert------
def dict_upsert(conn,table_name,d,key_name):
    if not is_table_and_op_allowed(table_name, 'update'):
        return f"ERROR: Update operation is not allowed on table '{table_name}'."

    pre_vals = d[key_name]

    c = conn.cursor()
    sql = 'select count(*) from {table_name} where {keys} = ?'.format(
                table_name=table_name,
                keys=key_name
    )    
    c.execute( sql, pre_vals )
    rcnt = int(c.fetchone()[0])

    try:
        if rcnt > 0 :
            return dict_update(conn,table_name,d,key_name)
        else:
            return dict_insert(conn, table_name, d)
    except:
        return "ERROR"
        


#----- delete operation

def dict_delete(conn, table_name, d, key_name):
    if not is_table_and_op_allowed(table_name, 'delete'):
        return f"ERROR: Delte operation is not allowed on table '{table_name}'."

    v = d.pop(key_name)
    vl=[v]
    pre_vals = tuple(vl)
    try:    
        sql = 'delete from {table_name} where {keys} = ?'.format(
                table_name=table_name,
                keys=key_name
            )    
        conn.execute( sql, pre_vals )
        return "OK: "+"{sql} {values}".format(sql=sql,values=pre_vals)
    except:
        return "SQL ERROR"

def json_delete(conn,table_name,j,key_name):
    dic_j = json.loads(j)
    return dict_delete(conn,table_name,dic_j,key_name)


#------ select operation

def json_select_all(conn, table_name):
#    conn.row_factory = dict_factory
    if not is_table_and_op_allowed(table_name, 'select'):
        return f"ERROR: Select operation is not allowed on table '{table_name}'."

    c = conn.cursor()
    rc = c.execute('SELECT * FROM '+table_name + ' LIMIT 100' )

    cols = [column[0] for column in rc.description]

    r = []
    for row in c.fetchall():
        r.append(dict(zip(cols,row)))
#        print(row)

#    return r
    return json.dumps(r,default=support_datetime_default)

def json_select_all_key(conn, table_name,d, key_name):
#    conn.row_factory = dict_factory
    if not is_table_and_op_allowed(table_name, 'select'):
        return f"ERROR: Select operation is not allowed on table '{table_name}'."

    v = d.pop(key_name)
    vl=[v]
    pre_vals = tuple(vl)

    c = conn.cursor()
    sql = 'select * from {table_name} where {keys} = ?'.format(
                table_name=table_name,
                keys=key_name
    )    
    rc = c.execute( sql, pre_vals )
    cols = [column[0] for column in rc.description]

    r = []
    for row in c.fetchall():
        r.append(dict(zip(cols,row)))

#    nous = c.fetchall()  

    return json.dumps(r,default=support_datetime_default)


def dict_select_all_key_fromto(conn, table_name,d, key_name,key_name_from_to=''):
    if not is_table_and_op_allowed(table_name, 'select'):
        return f"ERROR: Select operation is not allowed on table '{table_name}'."

    conn.row_factory = dict_factory

    v = d.pop(key_name)
    vl=[v]
    sql = f'select * from {table_name} where {key_name} = ? '

    if key_name_from_to:
        vl+=d.pop(key_name_from_to)
        sql += f'and {key_name_from_to} >= ? and {key_name_from_to} <= ?'

    pre_vals = tuple(vl)
    #return pre_vals

    c = conn.cursor()
    c.execute( sql, pre_vals )

    nous = c.fetchall()  

    return nous


def json_select_one(conn, table_name,d, key_name):
#    conn.row_factory = dict_factory
    if not is_table_and_op_allowed(table_name, 'select'):
        return f"ERROR: Select operation is not allowed on table '{table_name}'."

    v = d.pop(key_name)
    vl=[v]
    pre_vals = tuple(vl)

    c = conn.cursor()
    sql = 'select * from {table_name} where {keys} = ?'.format(
                table_name=table_name,
                keys=key_name
    )    
    c.execute( sql, pre_vals )

    nous = c.fetchone()  

    return json.dumps(nous,ensure_ascii=False)

def sql_connect(conn_str):
    return pyodbc.connect(conn_str)


#------Main-----
if __name__ == "__main__":

    conn_str = os.environ["CONN_STR"]
    #conn = pyodbc.connect(conn_str)
    conn = sql_connect(conn_str)

    # 全件（100件）を読む
    ret = json_select_all(conn, '商品マスタ2')
    fetch_data = json.loads(ret)   
    assert len(fetch_data) == 100
    print("OK...100件を読んだ")
    
    # インサート
    ret = dict_insert(conn, '商品マスタ2', {"コード":"99999-1","商品名":"テストデータ"})
    ret = json_select_all_key(conn, '商品マスタ2',{'コード':'99999-1'},'コード')
    fetch_data = json.loads(ret)
    #print(fetch_data)
    f=fetch_data[0]
    assert f.get('コード') == '99999-1'
    print("OK...INSERTできた")

    # update
    ret = dict_update(conn, '商品マスタ2', {"コード":"99999-1","商品名":"テストデータ更新"},'コード')
    ret = json_select_all_key(conn, '商品マスタ2',{'コード':'99999-1'},'コード')
    fetch_data = json.loads(ret)
    f=fetch_data[0]
    assert f.get('商品名') == 'テストデータ更新'
    print("OK...UPDATEできた")

    # update
    ret = dict_delete(conn, '商品マスタ2', {"コード":"99999-1"},'コード')
    ret = json_select_all_key(conn, '商品マスタ2',{'コード':'99999-1'},'コード')
    fetch_data = json.loads(ret)
    assert fetch_data == []
    print("OK...DELETEできた")

    conn.close()
