from datetime import date

class ICRN(object):
    @staticmethod
    def generate_icrn(reference: str, date_str: str,amount:str, biller_code: str = '216291') -> str:
        '''
        Note this is vanilla ICRN generator
        All bussiness rule should be applied before supplied to this calculator
        All inputs are string.

        :param reference, 8 bits:
        :param date_str in format yyyy/mm/dd:
        :param amount:
        :param biller_code:
        :return:
        '''
        assert(len(reference) == 9)
        str_array = []
        str_array.append(str(ICRN.MOD10V01(amount)))
        str_array.append(str(ICRN.MOD10V05(amount)))
        str_array.append(str(ICRN.date_offset(date_str)))
        str_array.append(reference)

        first_14bit = ''.join(str_array)

        str_array.append(str(ICRN.MOD10V10(first_14bit)))

        #print(str_array)

        return {'biller_code': biller_code,
                'icrn': ''.join(str_array)}

    @staticmethod
    def switch_two_one(input: int) -> int:
        if input == 1:
            return 2
        elif input == 2:
            return 1
        else:
            raise Exception("invalid input to switch_two_one: {}".format(input))

    @staticmethod
    def squash_above_ten(input:int) -> int:
        if input >= 10:
            input_1 = input // 10
            input_2 = input % 10
            return input_1 + input_2
        else:
            return input

    @staticmethod
    def MOD10V01(input: str) -> str:
        '''
        MOD10V01 Logic:
        1.	Working from right-to-left, multiply each digit by factors 2,1,2,1,2,1,…
        a.	If doubling a digit results in a number >= 10 (2 digits) then add the two digits together
        2.	Sum results of each digit
        3.	Mod 10 the sum
        4.	If mod10 of the sum = 0 then 0, otherwise 10 - Mod10

        :param input:
        :return:
        '''

        sum = 0
        multiplier = 2
        for c in reversed(input):
            sum += ICRN.squash_above_ten(int(c) * multiplier)
            multiplier = ICRN.switch_two_one(multiplier)

        if sum % 10 == 0:
            return 0
        else:
            return 10 - ( sum % 10 )

    @staticmethod
    def MOD10V05(input: str) -> str:
        '''
        MOD10V05 Logic:
        1.	Right-pad Amount Due with zeroes to a 12-digit string (including cents, excluding decimal point)
        2.	Multiply each digit by position-number in string (working left-to-right), i.e. multiply each digit by factors 1,2,3,4,5,6,7,8,9,10,11,12
        3.	Sum results of each digit
        4.	Mod 10 the sum

        :param input:
        :return:
        '''
        padded_input = '{0:0>12}'.format(input)
        sum = 0
        multiplier = 1
        for c in padded_input:
            sum += int(c) * multiplier
            multiplier += 1

        return sum % 10

    @staticmethod
    def date_offset(input: str) -> str:
        '''
        2.2.2.	Date Offset Calculated from Expiry Date
        This is a 3-digit number calculated as follows:
        1.	Take the Vehicle Expiry Date
        2.	Add 3 months to calculate the Final Payment Date
        3.	Subtract base date 01/01/2010 from the Final Payment Date
        4.	Take the last 3 digits of the result

        :param input:
        :return:
        '''

        yyyy = int(input[0:4])
        mm = int(input[5:7])
        dd = int(input[8:10])

        f_date = date(2010, 1, 1)
        l_date = date(yyyy,mm,dd)

        return str( (l_date - f_date).days )[-3:]

    @staticmethod
    def swtich_7_3_1(input:int) -> int:
        if input == 3:
            return 7
        elif input == 7:
            return 1
        elif input == 1:
            return 3
        else:
            raise Exception("invalid input to swtich_7_3_1: {}".format(input))

    @staticmethod
    def MOD10V10(input: str) -> str:
        '''
        MOD10V10 calculated across the other 14-digits
        The “other 14-digits” refers to the aabbbccccccccc value calculated by the previous steps.
        MOD10V10 Logic:
        1.	Working from right-to-left, multiply each digit by factors 7,3,1,7,3,1,7,3,1,7,3,1,7,3
        2.	Sum results of each digit
        3.	Mod 10 the sum
        4.	If mod10 of the sum = 0 then 0, otherwise 10 - mod10

        :param input:
        :return:
        '''

        assert(len(input) == 14)
        multiplier = 3
        sum = 0
        for c in input:
            sum += int(c) * multiplier
            multiplier = ICRN.swtich_7_3_1(multiplier)

        if sum % 10 == 0:
            return 0
        else:
            return 10 - ( sum % 10 )

if __name__ == '__main__':

    test_date = [

        { # test 1
            'input': {
                'reference' : '101961459',
                'amount': '20265',
                'date_str': '2018/09/29'
            },
                'output': '521931019614598'
        },
        { # test 2
            'input': {
                'reference': '101233757',
                'amount': '80080',
                'date_str': '2018/06/24'
            },
            'output': '520961012337571'
        },
        {  # test 3
            'input': {
                'reference': '101233757',
                'amount': '81650',
                'date_str': '2018/12/24'
            },
            'output': '482791012337575'
        },
        {  # test 4
            'input': {
                'reference': '100055860',
                'amount': '8600',
                'date_str': '2018/09/04'
            },
            'output': '921681000558607'
        },
        {  # test 4
            'input': {
                'reference': '106903657',
                'amount': '105630',
                'date_str': '2018/03/20'
            },
            'output': '850001069036578'
        },

    ]

    for d in test_date:
        expected = d['output']
        result = ICRN.generate_icrn(
                                    d['input']['reference'],
                                    d['input']['date_str'],
                                    d['input']['amount'])['icrn']
        print(expected,result)
        assert(expected == result)
