#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class CompilationError(RuntimeError):
    pass


class CompilationWarning(RuntimeWarning):
    pass


class UnexpectedIdentifier(CompilationError):
    pass
