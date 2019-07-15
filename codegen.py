import yaml
import os.path
import time
from version import version
import argparse
import re


parser = argparse.ArgumentParser(description='Generate the boilerplate for Tulip Indicators')
parser.add_argument('--old', help='use old defaults', action='store_true')
args = parser.parse_args()

build = int(time.time())

path_prefix = os.path.join(os.path.dirname(os.path.realpath(__file__)), '')

indicators = yaml.safe_load(open(path_prefix+'indicators.yaml'))


def declaration_start(name):
    return f'int ti_{name}_start(TI_REAL const *options)'
def declaration_plain(name):
    return f'int ti_{name}(int size, TI_REAL const *const *inputs, TI_REAL const *options, TI_REAL *const *outputs)'
def declaration_ref(name):
    return f'int DONTOPTIMIZE ti_{name}_ref(int size, TI_REAL const *const *inputs, TI_REAL const *options, TI_REAL *const *outputs)'
def declaration_stream_new(name):
    return f'int ti_{name}_stream_new(TI_REAL const *options, ti_stream **stream)'
def declaration_stream_run(name):
    return f'int ti_{name}_stream_run(ti_stream *stream, int size, TI_REAL const *const *inputs, TI_REAL *const *outputs)'
def declaration_stream_free(name):
    return f'void ti_{name}_stream_free(ti_stream *stream)'


with open(path_prefix+'indicators.h', 'w') as f:
    def declarations(indicator):
        name, (elab_name, type, inputs, options, outputs, features) = indicator
        result = '\n'.join([
            f'/* {name} */',
            f'/* Type: {type} */',
            f'/* Input arrays: {len(inputs)}    Options: {len(options)}    Output arrays: {len(outputs)} */',
            f'/* Inputs: [{", ".join(inputs)}] */',
            f'/* Options: {"["+", ".join(options)+"]" if options else "none"} */',
            f'/* Outputs: [{", ".join(outputs)}] */',
            f'DLLEXPORT extern {declaration_start(name)};',
            f'DLLEXPORT extern {declaration_plain(name)};',
        ] + ([
            f'DLLEXPORT extern {declaration_ref(name)};',
        ] if 'ref' in features else []) + ([
            f'DLLEXPORT extern {declaration_stream_new(name)};',
            f'DLLEXPORT extern {declaration_stream_run(name)};',
            f'DLLEXPORT extern {declaration_stream_free(name)};',
        ] if 'stream' in features else []) + [
            ''
        ])
        return result

    result = '\n'.join([
        '/* Generated by codegen.py */',
        '#pragma once',
        '',
        f'#define TI_VERSION "{version}"',
        f'#define TI_BUILD {build}',
        '',
        '#include <math.h>',
        '#include <assert.h>',
        '#include <string.h>',
        '#include <stdlib.h>',
        '',
        '#ifdef __cplusplus',
        'extern \"C\" {',
        '#endif',
        '',
        '#ifdef _WIN32',
        '    #ifdef BUILDING',
        '        #define DLLEXPORT __declspec(dllexport)',
        '    #else',
        '        #define DLLEXPORT __declspec(dllimport)',
        '    #endif',
        '#else',
        '    #define DLLEXPORT',
        '#endif',
        '',
        '#ifndef _WIN32',
        '    #define DONTOPTIMIZE __attribute__((optimize("O3")))',
        '#else',
        '    #define DONTOPTIMIZE __pragma("", off)',
        '#endif',
        '',
        'DLLEXPORT extern const char* ti_version();',
        'DLLEXPORT extern long int ti_build();',
        'DLLEXPORT extern int ti_indicator_count();',
        '',
        'typedef double TI_REAL;',
        'enum {TI_OKAY, TI_INVALID_OPTION, TI_OUT_OF_MEMORY};',
        'enum {TI_TYPE_OVERLAY=1, TI_TYPE_INDICATOR, TI_TYPE_MATH, TI_TYPE_SIMPLE, TI_TYPE_COMPARATIVE};',
        '#define TI_MAXINDPARAMS 10 /* No indicator will use more than this many inputs, options, or outputs. */',
        '',
        'struct ti_stream; typedef struct ti_stream ti_stream;',
        'typedef int (*ti_indicator_start_function)(TI_REAL const *options);',
        'typedef int (*ti_indicator_function)(int size, TI_REAL const *const *inputs, TI_REAL const *options, TI_REAL *const *outputs);',
        'typedef int (*ti_indicator_stream_new)(TI_REAL const *options, ti_stream **stream);',
        'typedef int (*ti_indicator_stream_run)(ti_stream *stream, int size, TI_REAL const *const *inputs, TI_REAL *const *outputs);',
        'typedef void (*ti_indicator_stream_free)(ti_stream *stream);',
        '',
        'typedef struct ti_indicator_info {',
        '    char *name;',
        '    char *full_name;',
        '    ti_indicator_start_function start;',
        '    ti_indicator_function indicator;',
        '    ti_indicator_function indicator_ref;',
        '    int type, inputs, options, outputs;',
        '    char *input_names[TI_MAXINDPARAMS];',
        '    char *option_names[TI_MAXINDPARAMS];',
        '    char *output_names[TI_MAXINDPARAMS];',
        '    ti_indicator_stream_new stream_new;',
        '    ti_indicator_stream_run stream_run;',
        '    ti_indicator_stream_free stream_free;',
        '} ti_indicator_info;',
        '',
        f'#define TI_INDICATOR_COUNT {len(indicators)}',
        'DLLEXPORT extern ti_indicator_info ti_indicators[];',
        'DLLEXPORT extern const ti_indicator_info *ti_find_indicator(const char *name);',
        '',
        'DLLEXPORT extern int ti_stream_run(ti_stream *stream, int size, TI_REAL const *const *inputs, TI_REAL *const *outputs);',
        'DLLEXPORT extern ti_indicator_info *ti_stream_get_info(ti_stream *stream);',
        'DLLEXPORT extern int ti_stream_get_progress(ti_stream *stream);',
        'DLLEXPORT extern void ti_stream_free(ti_stream *stream);',
        '\n'.join(map(declarations, indicators.items())),
        f'enum {{{", ".join(f"TI_INDICATOR_{name.upper()}_INDEX" for name in sorted(indicators))}}};',
        '#ifdef __cplusplus',
        '}',
        '#endif',
    ])
    print('codegen.py: indicators.h')
    f.write(result)

with open(path_prefix+'indicators_index.c', 'w') as f:
    def index_entry(indicator):
        name, (elab_name, type, inputs, options, outputs, features) = indicator
        result = '{' + ', '.join([
            f'"{name}"',
            f'"{elab_name}"',
            f'ti_{name}_start',
            f'ti_{name}',
            f'ti_{name}_ref' if 'ref' in features else '0', 
            f'TI_TYPE_{type.upper()}',
            f'{len(inputs)}',
            f'{len(options)}',
            f'{len(outputs)}',
            '{'+', '.join(list(map('"{}"'.format, inputs)) + ["0"])+'}',
            '{'+', '.join(list(map('"{}"'.format, options)) + ["0"])+'}',
            '{'+', '.join(list(map('"{}"'.format, outputs)) + ["0"])+'}',
            f'ti_{name}_stream_new' if 'stream' in features else '0',
            f'ti_{name}_stream_run' if 'stream' in features else '0',
            f'ti_{name}_stream_free' if 'stream' in features else '0',
        ]) + '}'
        return result

    result = '\n'.join([
        '#include "indicators.h"',
        'const char* ti_version() { return TI_VERSION; }',
        'long int ti_build() { return TI_BUILD; }',
        'int ti_indicator_count() { return TI_INDICATOR_COUNT; }',
        '',
        'struct ti_indicator_info ti_indicators[] = {',
        ',\n'.join(list(map(index_entry, sorted(indicators.items()))) + ['{0,0,0,0,0,0,0,0,0,{0,0},{0,0},{0,0},0,0,0}']),
        '};'
        '',
        'struct ti_stream {',
        '    int index;',
        '    int progress;',
        '};',
        '',
        'int ti_stream_run(ti_stream *stream, int size, TI_REAL const *const *inputs, TI_REAL *const *outputs) {',
        '    return ti_indicators[stream->index].stream_run(stream, size, inputs, outputs);',
        '}',
        '',
        'ti_indicator_info *ti_stream_get_info(ti_stream *stream) {',
        '    return ti_indicators + stream->index;',
        '}',
        '',
        'int ti_stream_get_progress(ti_stream *stream) {',
        '    return stream->progress;',
        '}',
        '',
        'void ti_stream_free(ti_stream *stream) {',
        '    ti_indicators[stream->index].stream_free(stream);',
        '}',
        '',
        'const ti_indicator_info *ti_find_indicator(const char *name) {',
        '    int imin = 0;',
        '    int imax = sizeof(ti_indicators) / sizeof(ti_indicator_info) - 2;',
        '',
        '    /* Binary search */',
        '    while (imax >= imin) {',
        '        const int i = (imin + ((imax-imin)/2));',
        '        const int c = strcmp(name, ti_indicators[i].name);',
        '        if (c == 0) {',
        '            return ti_indicators + i;',
        '        } else if (c > 0) {',
        '            imin = i + 1;',
        '        } else {',
        '            imax = i - 1;',
        '        }',
        '    }',
        '',
        '    return 0;',
        '}',
    ])
    print('codegen.py: indicators_index.c')
    f.write(result)

for indicator in indicators.items():
    name, (elab_name, type, inputs, options, outputs, features) = indicator
    file_path_c = os.path.join(path_prefix+'indicators', f'{name}.c')
    file_path_cc = os.path.join(path_prefix+'indicators', f'{name}.cc')

    nl = '\n'
    unpack_options = '\n    '.join(f'const TI_REAL {opt} = options[{i}];' for i, opt in enumerate(options))
    unpack_inputs = '\n    '.join(f'TI_REAL const *const {inp} = inputs[{i}];' for i, inp in enumerate(inputs))
    unpack_outputs = '\n    '.join(f'TI_REAL *{outp} = outputs[{i}];' for i, outp in enumerate(outputs))

    includes = [
        '#include "../indicators.h"',
        '#include "../utils/log.h"',
        '#include "../utils/minmax.h"',
    ] + ([
        '#include "../utils/localbuffer.h"',
    ] if args.old else [
        '#include "../utils/ringbuf.hh"',
        '',
        '#include <new>',
        '#include <exception>',
    ])

    base = [
        '',
        f'{declaration_start(name)} {{',
        f'    {unpack_options}',
        '',
        '    #error "return how shorter will the output be than the input"',
        '}',
        '',
        f'{declaration_plain(name)} try {{',
        f'    {unpack_inputs}',
        f'    {unpack_options}',
        f'    {unpack_outputs}',
        '',
        '    #error "don\'t forget to validate options"',
        '',
        '    #error "vectorized implementation goes here"',
        '',
        '    return TI_OKAY;',
        '} catch (std::bad_alloc& e) {',
        '    return TI_OUT_OF_MEMORY;',
        '}'
    ]

    ref = [
        '',
        f'{declaration_ref(name)} {{',
        f'    {unpack_inputs}',
        f'    {unpack_options}',
        f'    {unpack_outputs}',
        '',
        '    #error "don\'t forget to validate options"',
        '',
        '    #error "obviously correct implementation goes here"',
        '',
        '    return TI_OKAY;',
        '}',
    ]

    stream = [
        '',
        'struct ti_stream {',
        '    int index;',
        '    int progress;',
        '',
        '    struct {',
        f'        {(nl+" "*8).join(map("TI_REAL {};".format, options))}',
        '    } options;',
        '',
        '    struct {',
        '',
        '    } state;',
        '',
        '    struct {',
        '',
        '    } constants;',
    ] + ([
        '',
        '    BUFFERS(',
        '',
        '    )',
    ] if args.old else [
    ]) + [
        '};',
        '',
        f'{declaration_stream_new(name)} {{',
        f'    {unpack_options}',
        '',
        '    #error "don\'t forget to validate options"',
        '',
    ] + ([
        '    *stream = calloc(1, sizeof(**stream));',
    ] if args.old else [
        '    *stream = new(std::nothrow) ti_stream();',
    ]) + [
        '    if (!*stream) { return TI_OUT_OF_MEMORY; }',
        '',
        f'    (*stream)->index = TI_INDICATOR_{name.upper()}_INDEX;',
        f'    (*stream)->progress = -ti_{name}_start(options);',
        '',
        '\n'.join(map("    (*stream)->options.{0} = {0};".format, options)),
    ] + ([
        '',
        '    #error "don\'t forget to initialize buffers"',
        '',
        '    *stream = realloc(*stream, sizeof(**stream) + sizeof(TI_REAL) * BUFFERS_SIZE(*stream));',
        '    if (!stream) { return TI_OUT_OF_MEMORY; }',
    ] if args.old else [
        '',
        '    try {',
        '        #error "don\'t forget to initialize ringbuffers and any other storage"',
        '    } catch (std::bad_alloc& e) {',
        '        delete *stream;',
        '        return TI_OUT_OF_MEMORY;',
        '    }',
    ]) + [
        '',
        '    return TI_OKAY;',
        '}',
        '',
        f'{declaration_stream_free(name)} {{',
    ] + ([
        '    free(stream);',
    ] if args.old else [
        '    delete stream;',
    ]) + [
        '}',
        '',
        f'{declaration_stream_run(name)} {{',
        f'    {unpack_inputs}',
        f'    {unpack_outputs}',
        '    int progress = stream->progress;',
        '\n'.join(map("    const TI_REAL {0} = stream->options.{0};".format, options)),
        '',
        '    int i = 0;',
        '    #error "streaming implementation goes here"',
        '',
        '    stream->progress = progress;',
        '    #error "be sure to save all the state"',
        '',
        '    return TI_OKAY;',
        '}',
    ]

    path = file_path_c if args.old else file_path_cc
    if not os.path.exists(file_path_c) and not os.path.exists(file_path_cc):
        with open(path, 'w') as f:
            print(f'codegen.py: indicators/{os.path.basename(path)}')
            parts = includes + base + (ref if 'ref' in features else []) + (stream if 'stream' in features else [])
            f.write('\n'.join(parts))
            os.system(f'git add -N {path}')
    else:
        if os.path.exists(file_path_c):
            with open(file_path_c) as f:
                contents = f.read()
        elif os.path.exists(file_path_cc):
            with open(file_path_cc) as f:
                contents = f.read()

        should_add_ref = 'ref' in features and not re.search(f'ti_{name}_ref', contents)
        should_add_stream = 'stream' in features and not re.search(f'ti_{name}_stream', contents)
        tbd = (
            (ref if should_add_ref else []) +
            (stream if should_add_stream else [])
        )

    if tbd:
        if os.path.exists(file_path_c) and not args.old:
            print(f'codegen.py: renaming indicators/{os.path.basename(file_path_c)} -> indicators/{os.path.basename(path)}')
            os.system(f'git mv "{file_path_c}" "{path}"')
        with open(path, 'r') as f:
            lines = f.readlines()
        with open(path, 'a') as f:
            print(f'codegen.py: adding{" ref" if should_add_ref else ""}{" stream" if should_add_stream else ""} to indicators/{os.path.basename(path)}')
            f.write('\n'.join(['']+tbd))
            os.system(f'git add {path}')
