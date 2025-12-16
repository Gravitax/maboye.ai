# Test Suites Documentation

## Overview

This document describes the test suites available in the project and their purposes.

## Test Suite: Execution Workflow

Location: tests/execution_workflow/

### Purpose

Validates the execution of individual tools through predefined execution plans. These tests ensure that each tool can be called correctly and produces expected results.

### Test Categories

#### File Operations Tests

Tests for file system manipulation tools.

test_read_file_workflow validates reading file contents. The test verifies that the tool can open and read a file, and that the content is correctly captured in memory.

test_write_file_workflow validates writing content to files. The test ensures files are created at the specified path with correct content.

test_edit_file_workflow validates in-place file modification. The test replaces specific text in an existing file and verifies the replacement occurred.

test_file_info_workflow validates retrieval of file metadata. The test checks that file size, permissions, and timestamps can be retrieved.

test_ls_workflow validates directory listing functionality. The test ensures the tool returns a list of files and directories with their metadata.

#### Search Operations Tests

Tests for code and content search tools.

test_grep_workflow validates pattern matching in files. The test searches for a specific pattern and verifies matching lines are returned.

test_find_file_workflow validates finding files by name pattern. The test uses glob patterns to locate files matching specific criteria.

test_get_file_structure_workflow validates directory tree retrieval. The test ensures the tool can generate a hierarchical view of directory contents.

test_code_search_workflow validates syntax-aware code search. The test searches for code patterns like function definitions and verifies results.

#### Bash Operations Tests

Tests for shell command execution tools.

test_pwd_workflow validates current directory retrieval. The test executes the pwd command and verifies the path is correct.

test_git_status_workflow validates git repository status check. The test retrieves repository state including modified files and staging area.

test_git_log_workflow validates git commit history retrieval. The test fetches recent commits with their metadata.

#### Multi-Step Tests

Tests for complex workflows involving multiple sequential or parallel operations.

test_read_modify_write_workflow validates a two-step dependent workflow. The test reads a file, then writes modified content based on the read result. It verifies that step dependencies are respected.

test_sequential_operations_workflow validates a three-step chained workflow. The test creates two files sequentially, then lists the directory containing them. It ensures operations execute in order and results are visible to subsequent steps.

test_multi_action_step_workflow validates parallel action execution. The test creates multiple files simultaneously within a single step, verifying that parallel operations complete successfully.

### Validation Strategy

Each test verifies three aspects:

Execution success ensures the tool completed without errors.

Memory persistence confirms all tool calls and results are saved to conversation memory with correct metadata.

Result accuracy validates that tool outputs match expected values or patterns.

## Test Suite: Iterative Workflow

Location: tests/test_iterative_workflow.py

### Purpose

Validates the complete iterative agent workflow where the agent makes decisions based on previous results. These tests simulate real agent behavior with a mock LLM backend.

### Workflow Tested

The iterative workflow implements a loop where the agent receives a query, sends it to the LLM, receives tool calls or final text, executes tools, sends results back to the LLM, and repeats until completion.

### Test Scenarios

#### Architecture Analysis Scenario

test_iterative_analyze_architecture validates a complex multi-step analysis workflow.

The test sends a query asking to analyze the project architecture. The mock LLM responds with tool calls to list files, read the main entry point, and read core modules. After gathering information, it produces a final text analysis.

The test verifies at least three tool executions occurred, including list_files and read_file operations, and that the final response contains an architecture analysis.

#### Read and Summarize Scenario

test_iterative_read_summarize validates a simple two-step workflow.

The test asks to read and summarize a file. The mock LLM first calls read_file to get the content, then produces a text summary based on the content.

The test verifies exactly one tool execution occurred using read_file, and that the final response contains a summary.

#### Error Finding Scenario

test_iterative_find_errors validates a multi-grep workflow.

The test asks to find errors in the codebase. The mock LLM searches for ERROR patterns, then FIXME comments, and finally produces an error analysis report.

The test verifies at least two grep tool executions occurred and that the final response contains an error analysis.

#### Default Scenario

test_iterative_default_scenario validates the fallback workflow.

The test sends a simple generic query. The mock LLM executes a basic command like pwd and returns a completion message.

The test verifies at least one tool execution occurred and a response was produced.

### Termination Conditions Tests

#### Max Iterations Test

test_iterative_max_iterations validates that the agent stops after reaching the iteration limit.

The test runs an analysis with a reduced maximum iteration count. It verifies that the agent stops within the limit and doesn't exceed it.

#### Memory Persistence Test

test_iterative_memory_persistence validates that all conversation elements are saved.

The test runs a workflow and verifies that user queries, tool executions, and final responses are all present in memory with correct roles.

#### Tool Execution Results Test

test_iterative_tool_execution_results validates proper result capture.

The test verifies that each tool execution has non-empty content and metadata including tool name and success status.

### Key Differences from Execution Workflow Tests

The execution workflow tests use predefined plans where all steps are known upfront. The agent executes a fixed sequence without decision-making.

The iterative workflow tests simulate real agent behavior where the agent decides what to do next based on previous results. The mock LLM determines which tools to call and when to stop.

### Stagnation Detection

The iterative workflow includes stagnation detection that stops the agent if it repeats the same tool calls three times consecutively. This prevents infinite loops in case of agent errors.

## Test Data Organization

### Test Files Directory

tests/execution_workflow/test_files/ contains reference files used by tests including sample Python code, text files for grep testing, and nested directories for recursive operations.

### Expected Outputs Directory

tests/execution_workflow/expected_outputs/ contains reference outputs for comparison in tests.

### Generated Directory

tests/execution_workflow/generated/ stores files created during test execution. This directory is gitignored and automatically cleaned between test runs.

## Running Tests

All tests require the backend mock server running on localhost:8000. Tests must be executed from the project root directory to ensure proper module imports.

The execution workflow tests validate individual tool functionality in isolation.

The iterative workflow tests validate complete agent behavior including decision-making and multi-step reasoning.
