import tushare as ts 
import pandas as pd 
import numpy as np

from sklearn.svm import SVR
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier

from selection_and_timing.adjust_start_date import Closest_TraDt_2
from selection_and_timing.data_merge import get_temp_data

Model_Rf = RandomForestClassifier()

test_less_row = 25


#pd.set_option('display.max_columns', None)

year_list = range(2017, 2018)
quarter_list = range(1, 2)
start_list = ['2017-04-17', '2017-07-17', '2017-10-17', '2018-01-31']
end_list = ['2018-04-17', '2018-07-17', '2018-10-17', '2019-01-31']

temp_row = -1
temp_col = -1

x = []
y = []
x_temp = []


Qua_Dict = {1:'-04-27', 2:'-07-17', 3:'-10-17',4:'-04-17'}


df = pd.read_csv('selection_and_timing/stock_data.csv', converters={'code': '{:0>6}'.format}) #ts.get_profit_data(year, quarter)
print ('公司数', df.shape[0],'/n指标数', df.shape[1])
print ('1', df.shape)

def Drop_NA(tol_na, dataframe):
	'''
	如果一个指标超过N家公司都没有数据，就把该指标删除
	:param tol_na: tol_na = 20  # 一个指标可以最多容忍的tol_na个公司没有数据，否则drop掉
	:param dataframe:原始df
	:return:删了特定指标的df
	'''
	drop_list = list(df.isna().sum()[df.isna().sum() >= tol_na].index)
	dataframe = dataframe.drop(drop_list, axis = 1)
	return dataframe

df = Drop_NA(20, df)

df.dropna( axis=0, how='any', thresh=None, subset=None, inplace=True )
print ('2', df.shape)
df.sort_values( by="code" , ascending=True, inplace=True )
print ('3', df.shape)
df.drop_duplicates(['code','time_point'], inplace = True ) #根据code和time_point两个指标删除重复值
print ('4', df.shape)
df['yield'] = np.nan
print ('5', df.shape)
( temp_row, temp_col ) = df.shape
print (temp_row, temp_col)
temp_row = test_less_row ##################################################################
for row in range(0, temp_row):
	print ('row:',row)
	temp_stock_int = int(df.iloc[ row, 1 ])
	temp_stock = "%06d" % temp_stock_int
	temp_date = df.iloc[ row, -2 ]
	temp_df = ts.get_hist_data( temp_stock, start = temp_date, end = Closest_TraDt_2(temp_date) )
	#print (temp_df)
	temp_row2 = -1
	temp_col2 = -1
	( temp_row2, temp_col2 ) = temp_df.shape
	if temp_row2 > 100:
		yield_yoy = ( temp_df.iloc[ 0, 2 ] - temp_df.iloc[ -1, 2 ] ) / temp_df.iloc[ -1, 2 ]
		df.iloc[ row, -1 ] = yield_yoy

df.dropna( axis=0, how='any', thresh=None, subset=None, inplace=True )

def assert_allNumber(dataframe):
	'''
	判断dataframe里每列都是numeric data
	:param dataframe: 原始df
	:return: null
	'''
	list_noNumber = []
	for i in dataframe:
		try:
			float(dataframe[i].values[0])
		except ValueError:
			list_noNumber.append(i)
			print('{0} 不是numeric data，已删除'.format(i))
			continue
	dataframe = dataframe.drop(list_noNumber, axis= 1)
	return dataframe

df = assert_allNumber(df)

( temp_row, temp_col ) = df.shape
for i in range(0, temp_row):
	for j in range(3, temp_col-1):
		x_temp.append(df.iloc[i, j])
	x.append( x_temp )
	y.append( df.iloc[i, -1] )
	x_temp = []

print ('x=')
print (x)
print ('y=')
print (y)

MinMax = MinMaxScaler()
print('x shape', len(x))
x_new = MinMax.fit_transform(x)

x_train, x_test, y_train, y_test = train_test_split(x_new, y, test_size=0.25)
print ('y_train =')
print (y_train)
print ('y_test =')
print (y_test)



cv = StratifiedKFold(n_splits= 5, shuffle= True)
C = np.arange(0.5, 5, 0.5)
param_grid = dict(C = C)
kfold = StratifiedKFold(n_splits = 5, shuffle = True, random_state = 7)

model = SVR()
grid_search = GridSearchCV(model, param_grid, scoring = 'neg_mean_squared_error', n_jobs = -1, cv = kfold)
y_train = np.zeros(len(y_train))
grid_result = grid_search.fit(x_train, y_train)
print("Best: %f using %s" % ( grid_result.best_score_, grid_search.best_params_ ))

model = SVR(C = grid_search.best_params_['C'])


# print('xx',type(x_train))
# print('yy',type(y_train))
model.fit(x_train, y_train)
y_predict = model.predict(x_test)
print ('y_test', y_test)
print ('y_predict', y_predict)

###################################################################
row_choosing_stock = -1
col_choosing_stock = -1
def choosing_stock(the_year, the_quarter):
	x_choosing_stock = []
	x_temp_choosing_stock = []
	print (the_year, the_quarter)
	data_choosing_stock = get_temp_data(the_year, the_quarter)
	data_choosing_stock.dropna( axis=0, how='any', thresh=None, subset=None, inplace=True )
	data_choosing_stock.sort_values( by="code" , ascending=True, inplace=True )
	data_choosing_stock.drop_duplicates( ['code'], inplace = True )
	data_choosing_stock['yield'] = np.nan
	print(data_choosing_stock.shape)
	data_choosing_stock = assert_allNumber(data_choosing_stock)
	( row_choosing_stock, col_choosing_stock ) = data_choosing_stock.shape
	row_choosing_stock = test_less_row ######################################################
	for the_row in range(0, row_choosing_stock):


		for the_col in range(2, col_choosing_stock-1):
			x_temp_choosing_stock.append(data_choosing_stock.iloc[the_row, the_col])

		print('x temp shape 1', len(x_temp_choosing_stock))
		x_choosing_stock.append(x_temp_choosing_stock)

		print('x shape 2', len(x_choosing_stock))

		x_choosing_stock_new = MinMax.transform(x_choosing_stock)
		y_choosing_stock_predict = model.predict(x_choosing_stock_new)
		x_choosing_stock = []
		x_temp_choosing_stock = []
		data_choosing_stock.iloc[the_row, -1] = y_choosing_stock_predict

	data_choosing_stock.sort_values( by="yield", ascending=False, inplace=True )
	stock_list = data_choosing_stock[['code', 'name', 'yield']]

	print ('stock_list')
	print (stock_list)

##################################################################

choosing_stock(2018, 3)