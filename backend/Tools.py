from __future__ import print_function
'''
This file holds some functions that don't have any obvious other home
'''

def ValidateFields(d,reqFields,optFields=None):
        '''
        The function checkFields takes in inputs of:
        
        =========   =============================================================
        Variable    Type & Description
        =========   =============================================================
        d           dict of values that are part of structure
        reqFields   list of tuples in the form (fieldname,typepointer,min,max)
        optFields   list of other fieldnames
        =========   =============================================================
        
        required parameters are checked that they
        * exist
        * can be cast using the typepointer function pointer
        * is within the range (min,max)
        
        if a parameter is on the optional parameters list, it is ok-ed,
        but not value checked
        
        Additional parameters raise AttributeError
        
        '''
        #make a copy of d
        d=dict(d)
        
        #Required parameters
        for field,typepointer,min,max in reqFields:
            if field in d:
                #See if you can do a type cast using the conversion function pointer
                # You should get the same value back
                assert typepointer(d[field])==d[field],field+': failed type conversion, should be '+str(typepointer)
                #check the bounds if numeric input
                if typepointer in (float,int):
                    assert d[field]>=min and d[field]<=max,field+' (value: %g) not in the range [%g,%g]'%(d[field],min,max)
                #remove field from dictionary of terms left to check if no errors
                del d[field]
            else:
                raise AttributeError('Required field '+field+' not included')
        #Optional parameters (not strictly checked, just checked their existence)
        if optFields!=None:
            for field in optFields:
                if field in d:
                    del d[field]
        assert len(d)==0,'Unmatched fields found: '+str(d.keys())
        
    
if __name__=='__main__':
    pass