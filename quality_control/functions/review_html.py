#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 15:13:19 2026

@author: marina
"""

import os

def write_html_file(html_code, full_path):
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(html_code)
    print(f"HTML file created at: {full_path}")
    
    
def create_html_file(path):
    html_code = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>QC Review for {{ subject }}</title>

    <!-- Styles -->
    <link rel="stylesheet" href="{{ url_for('static', filename='style_v2.css') }}">
    
    <!-- Scripts -->
    <script src="{{ url_for('static', filename='script.js') }}"></script>
</head>
<body>
    <!-- Page Header -->
    <h1>Quality Control Review</h1>

    <div class="header">
        <h2>Subject: {{ subject }}</h2>
        <h2>Session: {{ session_id }}</h2>
        <div class="right-header">
            <div class="reports-group">Reviewing group: {{ group }}</div>
            <div class="reports-left">Reports Left to Review: {{ reports_left }}</div>
            <div class="revisor-id">Revisor ID: {{ revisor_id }}</div>
        </div>
    </div>

    <!-- Report Viewer -->
    <iframe src="{{ url_for('report', subject=subject, session_id = session_id) }}"></iframe>

    <!-- QC Form -->
    <form action="{{ url_for('qc', subject=subject, session_id = session_id) }}" method="post">
        <input type="hidden" name="registration" id="registration" value="">
        <input type="hidden" name="periodic" id="periodic" value="">

        <div class="form-container">

            <!-- Decision Buttons -->
            <div class="decision-section">
                <div class="decision-group">
                    <h3>Registration Error</h3>
                    <div class="decision-buttons" id="registration-buttons">
                        <button type="button" onclick="selectDecision('registration', 'pass')" class="yes">Pass</button>
                        <button type="button" onclick="selectDecision('registration', 'no_pass')" class="no">No Pass</button>
                        <button type="button" onclick="selectDecision('registration', 'maybe')" class="maybe">Maybe</button>
                    </div>
                </div>

                <div class="decision-group">
                    <h3>Periodic Errors</h3>
                    <div class="decision-buttons" id="periodic-buttons">
                        <button type="button" onclick="selectDecision('periodic', 'pass')" class="yes">Pass</button>
                        <button type="button" onclick="selectDecision('periodic', 'no_pass')" class="no">No Pass</button>
                        <button type="button" onclick="selectDecision('periodic', 'maybe')" class="maybe">Maybe</button>
                    </div>
                </div>
            </div>

            <!-- Comment Section -->
            <div class="comment-section">
                <h3>Comment</h3>
                <textarea name="message" id="message" placeholder="Add your comment here..." rows="3" cols="60"></textarea>
            </div>

            <!-- Control Buttons -->
            <div class="control-buttons">
                <button type="button" class="exit" onclick="confirmExit()">Exit</button>
                <button type="submit" id="nextButton" disabled>Next</button>
            </div>
        </div>
    </form>
</body>
</html>

    """
    
    os.chdir(path)
    print('Changed path to: ', path)
    path = os.path.join(path, 'templates')
    os.makedirs(path, exist_ok = True)
    file_name = "review.html"
    write_html_file(html_code, os.path.join(path, file_name))
