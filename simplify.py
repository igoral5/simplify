# -*- coding: utf-8 -*-
'''
Created on 5 янв. 2017 г.
Упрощение выражения вида P1+P2+...=...PN
где PN выражение вида ax^k
где a - число с плавающей точкой;
k - целое число;
x - переменная (переменных у одного слагаемого может быть несколько).
Например, может быть дано уравнение следующего вида:
x^2 + 3.5xy + y = y^2 - xy + y
Оно должно быть приведено к виду:
x^2 - y^2 + 4.5xy = 0
@author: igor
'''

from enum import Enum
import re
import unittest

class Token(Enum):
    END = 0
    NAME = 1
    NUMBER = 2
    PLUS = '+'
    MINUS = '-'
    MUL = '*'
    POWER = '^'
    ASSIGN = '='
    LP = '('
    RP = ')'

class ParseError(RuntimeError):
    pass

class Term(object):
    """Реализует выражения вида 2x^2"""
    def __init__(self):
        self.koeff = 1.0
        self.names= {}
    
    def as_tuple(self):
        self._canon()
        if self.names:
            return tuple((name, power) for name, power in sorted(self.names.items()))
        else:
            return (('',0),)
    
    def __mul__(self, other):
        self._canon()
        other._canon()
        term = Term()
        term.names = self.names.copy()
        term.koeff = self.koeff
        for name in other.names:
            if name in term.names:
                term.names[name] += other.names[name]
            else:
                term.names[name] = other.names[name]
        term.koeff *= other.koeff
        term._canon()
        return term
    
    def __neg__(self):
        self._canon()
        term = Term()
        term.names = self.names.copy()
        term.koeff = self.koeff * -1 
        return term
    
    def _canon(self):
        names = {name: power for name, power in self.names.items() if name and power}
        self.names = names
        
    
    def __str__(self):
        self._canon()
        term = ''
        if self.koeff != 0.0:
            for name, power in sorted(self.names.items()):
                if power == 1:
                    term += '%s' % name
                else:
                    term += '%s^%d' % (name, power)
            if term:
                if abs(self.koeff) != 1.0:
                    term = str(self.koeff) + term
            else:
                term = str(self.koeff)
            if self.koeff < 0 and term[0] != '-':
                term = '-' + term 
        return term
         
class Polynomial(object):
    """Реализует выражение вида 3x^2y+5zy^3"""
    def __init__(self):
        self.terms = {}
    
    def add_term(self, term):
        key = term.as_tuple()
        if key in self.terms:
            self.terms[key].koeff += term.koeff
        else:
            self.terms[key] = term
        
    def __add__(self, other):
        polynom = Polynomial()
        polynom.terms = self.terms.copy()
        for key in other.terms:
            if key in polynom.terms:
                polynom.terms[key].koeff += other.terms[key].koeff
            else:
                polynom.terms[key] = other.terms[key]
        polynom._canon()
        return polynom
    
    def __sub__(self, other):
        polynom = Polynomial()
        polynom.terms = self.terms.copy()
        for key in other.terms:
            if key in polynom.terms:
                polynom.terms[key].koeff -= other.terms[key].koeff
            else:
                polynom.terms[key] = -other.terms[key]
        polynom._canon()
        return polynom
    
    def __mul__(self, other):
        polynom = Polynomial()
        for other_key in other.terms:
            for self_key in self.terms:
                term = self.terms[self_key] * other.terms[other_key]
                polynom.add_term(term)
        polynom._canon()
        return polynom
    
    def __neg__(self):
        polynom = Polynomial()
        for key in self.terms:
            term = -self.terms[key]
            polynom.terms[term.as_tuple()] = term
        return polynom
    
    def _canon(self):
        terms = {key: term for key, term in self.terms.items() if term.koeff != 0.0}
        self.terms = terms
        

    def __str__(self):
        self._canon()
        terms = []
        for key in sorted(self.terms):
            terms.append(str(self.terms[key]))
        s = ''
        for term in filter(None, terms):
            if s:
                if term[0] == '-':
                    s += term
                else:
                    s += '+' + term
            else:
                s += term
        if s:
            return s
        else:
            return '0'

class Simplify(object):
    """Simplify expression"""
    def __init__(self, expression):
        self.expression = expression
        self.index = 0
        self.curr_token = Token.END
        self.float_value = 0.0
        self.name_value = ''
        self.template_float = re.compile(r'^[-+]?((\d+\.?\d*)|(\d*\.?\d+))([eE][-+]?\d+)?')
        self.template_int = re.compile(r'^[-+]?\d+')
    
    def __call__(self):
        if self.expression:
            self.get_token()
            return str(self.full(False))+'=0'
        else:
            raise ParseError('Empty expression')
    
    def full(self, get):
        left = self.expr(get)
        if self.curr_token != Token.ASSIGN:
            raise ParseError('= expected')
        right = self.expr(True)
        return left - right
    
    def expr(self, get):
        left = self.term(get)
        while True:
            if self.curr_token == Token.PLUS:
                left = left + self.term(True)
            elif self.curr_token == Token.MINUS:
                left = left - self.term(True)
            else:
                return left
    
    def term(self, get):
        left = self.prim(get)
        while True:
            if self.curr_token == Token.MUL:
                left = left * self.prim(True)
            elif self.curr_token == Token.NAME:
                left = left * self.prim(False)
            elif self.curr_token == Token.NUMBER:
                left = left * self.prim(False)
            elif self.curr_token == Token.LP:
                left = left * self.prim(False)
            else:
                return left
    
    def prim(self, get):
        if get:
            self.get_token()
        if self.curr_token == Token.NUMBER:
            self.get_token()
            term = Term()
            if self.curr_token == Token.POWER:
                exp = self.get_int()
                term.koeff = pow(self.float_value, exp)
                self.get_token()
            else:
                term.koeff = self.float_value
            polynom = Polynomial()
            polynom.add_term(term)
            return polynom
        elif self.curr_token == Token.NAME:
            name = self.name_value
            self.get_token()
            term = Term()
            if self.curr_token == Token.POWER:
                exp = self.get_int()
                term.names[name] = exp
                self.get_token()
            else:
                term.names[name] = 1
            polynom = Polynomial()
            polynom.add_term(term)
            return polynom
        elif self.curr_token == Token.MINUS:
            return -self.prim(True)
        elif self.curr_token == Token.LP:
            val = self.expr(True)
            if self.curr_token != Token.RP:
                raise ParseError(') expected')
            self.get_token()
            return val
        else:
            raise ParseError('Primary excepted')
        
    def get_token(self):
        while self.index < len(self.expression) and self.expression[self.index].isspace():
            self.index += 1
        if self.index < len(self.expression):
            if self.expression[self.index].isalpha():
                self.curr_token = Token.NAME
                self.name_value = self.expression[self.index]
                self.index += 1
            elif self.expression[self.index].isdigit() or self.expression[self.index] == '.':
                self.curr_token = Token.NUMBER
                self.float_value = self.get_float()
            elif self.expression[self.index] == '+':
                self.curr_token = Token.PLUS
                self.index += 1
            elif self.expression[self.index] == '-':
                self.curr_token = Token.MINUS
                self.index += 1
            elif self.expression[self.index] == '*':
                self.curr_token = Token.MUL
                self.index += 1
            elif self.expression[self.index] == '^':
                self.curr_token = Token.POWER
                self.index += 1
            elif self.expression[self.index] == '=':
                self.curr_token = Token.ASSIGN
                self.index += 1
            elif self.expression[self.index] == '(':
                self.curr_token = Token.LP
                self.index += 1
            elif self.expression[self.index] == ')':
                self.curr_token = Token.RP
                self.index += 1
            else:
                raise ParseError('Bad token')
        else:
            self.curr_token = Token.END
    
    def get_float(self):
        res = self.template_float.match(self.expression[self.index:])
        if res:
            self.index += len(res.group(0))
            return float(res.group(0))
        else:
            raise ParseError('Bad float')
    
    def get_int(self):
        res = self.template_int.match(self.expression[self.index:])
        if res:
            self.index += len(res.group(0))
            return int(res.group(0))
        else:
            raise ParseError('Bad int')

class TestSimplify(unittest.TestCase):
    
    def test_primary_without_equals(self):
        simplify = Simplify('1')
        with self.assertRaises(ParseError):
            simplify()
    
    def test_primary_without_right_side(self):
        simplify = Simplify('1=')
        with self.assertRaises(ParseError):
            simplify()
    
    def test_primary(self):
        simplify = Simplify('1=0')
        self.assertEqual(simplify(), '1.0=0')
    
    def test_primary_move_from_right(self):
        simplify = Simplify('0=1')
        self.assertEqual(simplify(), '-1.0=0')
    
    def test_primary_add(self):
        simplify = Simplify('2+3=0')
        self.assertEqual(simplify(), '5.0=0')
    
    def test_primary_mul(self):
        simplify = Simplify('2*3=0')
        self.assertEqual(simplify(), '6.0=0')
    
    def test_primary_pow(self):
        simplify = Simplify('2^3=0')
        self.assertEqual(simplify(), '8.0=0')
    
    def test_primary_brackets(self):
        simplify = Simplify('2*(3+1)=0')
        self.assertEqual(simplify(), '8.0=0')
    
    def test_primary_brackets_pow(self):
        simplify = Simplify('(2+1)^2=0')
        with self.assertRaises(ParseError):
            simplify()
    
    def test_name_without_equals(self):
        simplify = Simplify('x')
        with self.assertRaises(ParseError):
            simplify()
    
    def test_name_without_right_side(self):
        simplify = Simplify('x=')
        with self.assertRaises(ParseError):
            simplify()
    
    def test_name(self):
        simplify = Simplify('x=0')
        self.assertEqual(simplify(), 'x=0')
    
    def test_name_move_from_right(self):
        simplify = Simplify('0=x')
        self.assertEqual(simplify(), '-x=0')
    
    def test_name_add_same(self):
        simplify = Simplify('x+x=0')
        self.assertEqual(simplify(), '2.0x=0')
    
    def test_name_add_different(self):
        simplify = Simplify('x+y=0')
        self.assertEqual(simplify(), 'x+y=0')
    
    def test_name_sub_same(self):
        simplify = Simplify('5x-3x=0')
        self.assertEqual(simplify(), '2.0x=0')
    
    def test_name_sub_differnt(self):
        simplify = Simplify('5x-3y=0')
        self.assertEqual(simplify(), '5.0x-3.0y=0')
    
    def test_name_mul(self):
        simplify = Simplify('xy=0')
        self.assertEqual(simplify(), 'xy=0')
    
    def test_name_pow(self):
        simplify = Simplify('x^2=0')
        self.assertEqual(simplify(), 'x^2=0')
    
    def test_name_brackets(self):
        simplify = Simplify('(x+y)*(x-y)=0')
        self.assertEqual(simplify(), 'x^2-y^2=0')
    
    def test_name_brackets_without_mul(self):
        simplify = Simplify('(x+y)(x-y)=0')
        self.assertEqual(simplify(), 'x^2-y^2=0')
    
    def test_name_brackets_pow(self):
        simplify = Simplify('(x+y)^2=0')
        with self.assertRaises(ParseError):
            simplify()
    
    def test_name_unary_minus(self):
        simplify = Simplify('x+y=-(x+y)')
        self.assertEqual(simplify(), '2.0x+2.0y=0')
    
    def test_expression(self):
        simplify = Simplify('3x^2y=0')
        self.assertEqual(simplify(), '3.0x^2y=0')
    
    def test_expression_add(self):
        simplify = Simplify('3x^2y + x^3y + 2x^2y=0')
        self.assertEqual(simplify(), '5.0x^2y+x^3y=0')
    
    def test_expression_mul(self):
        simplify = Simplify('(3x+4)*(2y^2+5)=0')
        self.assertEqual(simplify(), '20.0+15.0x+6.0xy^2+8.0y^2=0')
    
    def test_expression_with_space(self):
        simplify = Simplify('x^2 + 3.5xy + y = y^2 - xy + y')
        self.assertEqual(simplify(), '4.5xy+x^2-y^2=0')
    
    def test_expression_brackets_pow(self):
        simplify = Simplify('(x^2 + 3.5xy + y)^2 = y^2 - xy + y')
        with self.assertRaises(ParseError):
            simplify()
            
    def test_expression_bad_token(self):
        simplify = Simplify('abc$=0')
        with self.assertRaises(ParseError):
            simplify()
            
    def test_expression_not_closed_bracket(self):
        simplify = Simplify('((3x+5)*(z-1)=0')
        with self.assertRaises(ParseError):
            simplify()
    
    def test_primary_unary_minus(self):
        simplify = Simplify('-7=0')
        self.assertEqual(simplify(), '-7.0=0')
    
    def test_primary_unary_minus_right_side(self):
        simplify = Simplify('0=-7')
        self.assertEqual(simplify(), '7.0=0')
        
           
if __name__ == '__main__':
    unittest.main()      
        
        

    