# coding=UTF-8
# mapping tells the next functions where to get the data for each row
# each key in a mapping must return a function that takes
# the current row and the SimpleCSVGrid object
# the function must return the OFX data for that field.

# NOTE I thought about simply having a dicionary from key fields to column numbers
# but that was not flexible enough to combine column data dynamically
# in order to get custom data from the CSV file.
# (example Memo/Description/BankID/Account id in the yodlee data)

"""
    Mappings API.

    csvutils provides the functions fromCSVCol,xmlize and the grid that holds the csv data.
    fromCSVCol(row,grid,column)
        row: the row number
        grid: the csv data
        column: the case sensitive column header

        returns the csv data for that location

    a mapping is a dictionary of functions.  The exporters call the function for each key
    in the dictionary.  You are free to use any functions or custom logic to return whatever
    data you prefer so that you get the correct data in the fields required by the export format.
    The format of the function that must be returned is:

    def custfunc(row,grid)

    If you have a one-to-one mapping for a key to the CSV data, you can easily just use fromCSVCol.

    Example:

    'CHECKNUM':lambda row,grid: fromCSVCol(row,grid,'Check Number')

    Special parameters for import use these keys:

        delimiters: delimiter for CSV, default to ','
        skip_last: number of lines to skip at the end of the CSV file, default to 0

    OFX export uses these keys:

        skip: not used in export but tells the exporter to skip a row.  Useful for split data (ofx can't handle split data).
        BANKID: the id of the bank
        ACCTID: the account id
        DTPOSTED: date the transaction was posted (YYYYMMDD)
        TRNAMT: amount of transaction
        FITID: a unique transaction identifier (for avoiding duplicate imports)
        PAYEE: who the transaction was posted to/from
        MEMO: the memo
        CURDEF: currency def.  e.g. USD
        CHECKNUM: check number

    QIF export uses these keys:
        split: tells exporter this row is part of a parent transaction
            (row must have be preceded by parent) return True or False
        Account: The name of the account
        AccountDscr: A description for the account
        Date: date in mm/dd/YYYY or mm/dd/YY
        Payee: the transaction payee
        Memo: the memo
        Category: the category.  Imports as the expense account usually.
        Class: optional class data.  Return '' if unused
        Amount: transaction amount
        Number: check number 

    mapping dict format
    {'_params':<special parameters>, 'QIF':<the qif mapping>, 'OFX':<the ofx mapping>}

    The last line in this file tells csv2ofx about your mappings.
    You may add as many as you like.

    all_mappings={"Mapping Description":<the mapping>, ...}


"""

from csvutils import *


def yodlee_dscr(row,grid):
    " use user description for payee 1st, the original description"
    od=fromCSVCol(row,grid,'Original Description')
    ud=fromCSVCol(row,grid,'User Description')
    if len(ud)>0:
        return "%s - %s" % (od,ud)
    return od

def yodlee_memo(row,grid):
    memo=fromCSVCol(row,grid,'Memo') # sometimes None
    cat=fromCSVCol(row,grid,'Category')
    cls=fromCSVCol(row,grid,'Classification')
    if len(memo)>0:
        return "%s - %s - %s" % ( memo, cat, cls)
    return "%s - %s" % ( cat, cls )

def toOFXDate(date, format='%d/%m/%y'):
    return datetime.strptime(date,format).strftime('%Y%m%d')

yodlee = {

    'OFX':{
        'skip':lambda row,grid: fromCSVCol(row,grid,'Split Type') == 'Split',
        'BANKID':lambda row,grid: fromCSVCol(row,grid,'Account Name').split(' - ')[0],
        'ACCTID':lambda row,grid: fromCSVCol(row,grid,'Account Name').split(' - ')[-1], 
        'DTPOSTED':lambda row,grid: toOFXDate(fromCSVCol(row,grid,'Date')),
        'TRNAMT':lambda row,grid: fromCSVCol(row,grid,'Amount'),
        'FITID':lambda row,grid: fromCSVCol(row,grid,'Transaction Id'),
        'PAYEE':lambda row,grid: yodlee_dscr(row,grid),
        'MEMO':lambda row,grid: yodlee_memo(row,grid),
        'CURDEF':lambda row,grid: fromCSVCol(row,grid,'Currency'),
        'CHECKNUM':lambda row,grid: fromCSVCol(row,grid,'Transaction Id') 
    },
    'QIF':{
        'split':lambda row,grid: fromCSVCol(row,grid,'Split Type') == 'Split',
        'Account':lambda row,grid: fromCSVCol(row,grid,'Account Name'),
        'AccountDscr':lambda row,grid: ' '.join(fromCSVCol(row,grid,'Account Name').split('-')[1:]),
        'Date':lambda row,grid: fromCSVCol(row,grid,'Date'),
        'Payee':lambda row,grid: fromCSVCol(row,grid,'Original Description'),
        'Memo':lambda row,grid: fromCSVCol(row,grid,'User Description') + ' ' + fromCSVCol(row,grid,'Memo'),
        'Category':lambda row,grid: fromCSVCol(row,grid,'Category')+'-'+fromCSVCol(row,grid,'Classification'),
        'Class':lambda row,grid: '', 
        'Amount':lambda row,grid: fromCSVCol(row,grid,'Amount'),
        'Number':lambda row,grid: fromCSVCol(row,grid,'Transaction Id')
    }
}

cu = {
    'OFX':{
        'skip':lambda row,grid: False,
        'BANKID':lambda row,grid: 'Credit Union',
        'ACCTID':lambda row,grid: 'My Account',
        'DTPOSTED':lambda row,grid: toOFXDate(fromCSVCol(row,grid,'Date')),
        'TRNAMT':lambda row,grid: fromCSVCol(row,grid,'Amount').replace('$',''),
        'FITID':lambda row,grid: row,
        'PAYEE':lambda row,grid: fromCSVCol(row,grid,'Description'),
        'MEMO':lambda row,grid: fromCSVCol(row,grid,'Comments'),
        'CURDEF':lambda row,grid: 'USD',
        'CHECKNUM':lambda row,grid: fromCSVCol(row,grid,'Check Number')
    },
    'QIF':{
        'split':lambda row,grid:False,
        'Account':lambda row,grid: 'Credit Union',
        'AccountDscr':lambda row,grid: 'Credit Union Account',
        'Date':lambda row,grid: fromCSVCol(row,grid,'Date'),
        'Payee':lambda row,grid: fromCSVCol(row,grid,'Description'),
        'Memo':lambda row,grid: fromCSVCol(row,grid,'Comments'),
        'Category':lambda row,grid:'Unclassified',
        'Class':lambda row,grid:'',
        'Amount':lambda row,grid:fromCSVCol(row,grid,'Amount'),
        'Number':lambda row,grid:fromCSVCol(row,grid,'Check Number')        
    }
}

def ubs_toOFXDate(date):
    return datetime.strptime(date,'%d.%m.%Y').strftime('%Y%m%d')

def ubs_toQIFDate(date):
    return datetime.strptime(date,'%d.%m.%Y').strftime('%m/%d/%Y')

def ubs_toAmount(debit,credit):
    amount = 0
    if debit:
      amount -= float(debit.replace('\'',''))
    if credit:
      amount += float(credit.replace('\'',''))
    return amount

def ubs_toPayee(enteredby,recipient,description):
    if enteredby:
      return enteredby
    elif recipient:
      return recipient
    elif description:
      return description
    else:
      return 'UBS'

def ubs_toDescription(desc1,desc2,desc3):
    return ' / '.join(filter(None, [desc1,desc2,desc3]))

ubs = {
    '_params':{
        'delimiter': ';',
        'skip_last': 1
    },
    'OFX':{
        'skip':lambda row,grid: False,
        'BANKID':lambda row,grid: 'UBS',
        'ACCTID':lambda row,grid: fromCSVCol(row,grid,'Description'),
        'DTPOSTED':lambda row,grid: ubs_toOFXDate(fromCSVCol(row,grid,'Value date')),
        'TRNAMT':lambda row,grid: ubs_toAmount(fromCSVCol(row,grid,'Debit'),fromCSVCol(row,grid,'Credit')),
        'FITID':lambda row,grid: row,
        'PAYEE':lambda row,grid: ubs_toPayee(fromCSVCol(row,grid,'Entered by'),fromCSVCol(row,grid,'Recipient')),
        'MEMO':lambda row,grid: ubs_toDescription(fromCSVCol(row,grid,'Description 1'),
                                                  fromCSVCol(row,grid,'Description 2'),
                                                  fromCSVCol(row,grid,'Description 3')),
        'CURDEF':lambda row,grid: fromCSVCol(row,grid,'Ccy.'),
        'CHECKNUM':lambda row,grid: ''
    },
    'QIF':{
        'split':lambda row,grid:False,
        'Account':lambda row,grid: 'UBS',
        'AccountDscr':lambda row,grid: fromCSVCol(row,grid,'Description'),
        'Date':lambda row,grid: ubs_toQIFDate(fromCSVCol(row,grid,'Value date')),
        'Payee':lambda row,grid: ubs_toPayee(fromCSVCol(row,grid,'Entered by'),
                                             fromCSVCol(row,grid,'Recipient'),
                                             fromCSVCol(row,grid,'Description 3')),
        'Memo':lambda row,grid: ubs_toDescription(fromCSVCol(row,grid,'Description 1'),
                                                  fromCSVCol(row,grid,'Description 2'),
                                                  fromCSVCol(row,grid,'Description 3')),
        'Category':lambda row,grid:'Unclassified',
        'Class':lambda row,grid:'',
        'Amount':lambda row,grid: ubs_toAmount(fromCSVCol(row,grid,'Debit'),fromCSVCol(row,grid,'Credit')),
        'Number':lambda row,grid: ''        
    }
}

def msmoney_memo(row,grid):
    memo=fromCSVCol(row,grid,'Memo') # sometimes None
    cat=fromCSVCol(row,grid,'Category')
    cls=fromCSVCol(row,grid,'Projects')
    if len(memo)>0:
        return "%s - %s - %s" % ( memo, cat, cls )
    return "%s - %s" % (cat, cls)

msmoneyrep = {

    'OFX':{
        'skip':lambda row,grid: fromCSVCol(row,grid,'Split Type') == 'Split',
        'BANKID':lambda row,grid: fromCSVCol(row,grid,'Account Name').split(' - ')[0],
        'ACCTID':lambda row,grid: fromCSVCol(row,grid,'Account Name').split(' - ')[-1],
        'DTPOSTED':lambda row,grid: toOFXDate(fromCSVCol(row,grid,'Date')),
        'TRNAMT':lambda row,grid: fromCSVCol(row,grid,'Amount'),
        'FITID':lambda row,grid: row,
        'PAYEE':lambda row,grid: fromCSVCol(row,grid,'Payee'),
        'MEMO':lambda row,grid: msmoney_memo(row,grid),
        'CURDEF':lambda row,grid: fromCSVCol(row,grid,'Currency'),
        'CHECKNUM':''
    },
    'QIF':{
        'split':lambda row,grid: fromCSVCol(row,grid,'Date') == '', #split should be determined by absence of date and other fields.
        'Account':lambda row,grid: fromCSVCol(row,grid,'Account'),
        'AccountDscr':lambda row,grid: fromCSVCol(row,grid,'Account'),
        'Date':lambda row,grid: toOFXDate(fromCSVCol(row,grid,'Date')),
        'Payee':lambda row,grid: parse_payee(row,grid),
        'Memo':lambda row,grid: fromCSVCol(row,grid,'C') + ': ' + fromCSVCol(row,grid,'Memo'),
        'Category':lambda row,grid: fromCSVCol(row,grid,'Category'),
        'Class':lambda row,grid: fromCSVCol(row,grid,'Projects'),
        'Amount':lambda row,grid: fromCSVCol(row,grid,'Amount'),
        'Number':lambda row,grid: fromCSVCol(row,grid,'Num')
    }
}

creditcardbradesco = {

    'OFX':{
        'skip':lambda row,grid: False,
        'BANKID':lambda row,grid:'Bradesco',
        'ACCTID':lambda row,grid:'Cartao de Credito Bradesco',
        'DTPOSTED':lambda row,grid: toOFXDate(fromCSVCol(row,grid,'Data'), '%d/%m/%Y'),
        'TRNAMT':lambda row,grid: fromCSVCol(row,grid,'R$'),
        'FITID':lambda row,grid: row,
        'PAYEE':lambda row,grid:'',
        'MEMO':lambda row,grid: fromCSVCol(row,grid,'Histórico'),
        'CURDEF':lambda row,grid:'BRL',
        'CHECKNUM':lambda row,grid:''
    },
    'QIF':{
        'split':lambda row,grid: fromCSVCol(row,grid,'Date') == '', #split should be determined by absence of date and other fields.
        'Account':lambda row,grid: fromCSVCol(row,grid,'Account'),
        'AccountDscr':lambda row,grid: fromCSVCol(row,grid,'Account'),
        'Date':lambda row,grid: toOFXDate(fromCSVCol(row,grid,'Date')),
        'Payee':lambda row,grid: parse_payee(row,grid),
        'Memo':lambda row,grid: fromCSVCol(row,grid,'C') + ': ' + fromCSVCol(row,grid,'Memo'),
        'Category':lambda row,grid: fromCSVCol(row,grid,'Category'),
        'Class':lambda row,grid: fromCSVCol(row,grid,'Projects'),
        'Amount':lambda row,grid: fromCSVCol(row,grid,'Amount'),
        'Number':lambda row,grid: fromCSVCol(row,grid,'Num')
    }
}

all_mappings = {'Yodlee':yodlee, 'Credit Union':cu, 'UBS':ubs, 'MS Money Report (CSV)':msmoneyrep }