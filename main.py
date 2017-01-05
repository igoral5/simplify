#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-
'''
Created on 4 янв. 2017 г.
Driver for simplify.py
@author: igor
'''
import readline
import traceback
from simplify import Simplify, ParseError
import argparse
import sys

argparser = argparse.ArgumentParser(description='Simplify expression')
argparser.add_argument('-f', '--file', help='Input file')
args = argparser.parse_args()

def main():
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as fr:
                with open(args.file + '.out', 'w', encoding='utf-8') as fw:
                    for line in fr:
                        try:
                            simplify = Simplify(line)
                            print(simplify(), file=fw)
                        except ParseError as e:
                            print('ParseError:', e, file=fw)
        except Exception as e:
            print(e, file=sys.stderr)
            sys.exit()
    else:
        while True:
            try:
                expression = input('Expression: ')
                simplify = Simplify(expression)
                print(simplify())
            except EOFError:
                print()
                sys.exit()
            except Exception:
                traceback.print_exc()
                
if __name__ == '__main__':
    main()

                