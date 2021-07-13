# modbus-reader
modbus reader automation tool. 
limits entries per csv file to user specified amount. after amount is exceeded, will switch to new csv file. 

supports reading from multiple devices. takes json schema as follows:
{
  "<device 1 address>": [<register 1>, <register 2>, ...],
  "<device 2 address>": [<register 3>, <register 4>, ...]
}

see "pressure.json" for example. 

