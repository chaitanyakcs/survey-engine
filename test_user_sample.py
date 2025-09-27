#!/usr/bin/env python3
"""
Test the user's exact malformed JSON sample
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.generation_service import GenerationService
from unittest.mock import MagicMock
import json

def test_user_exact_sample():
    """Test the user's exact malformed JSON sample that was only parsing 2 questions"""

    mock_db = MagicMock()
    service = GenerationService(mock_db)

    # User's exact sample from logs
    user_sample = '''{ "
title
": "
Enterprise
 Cybersecurity
 Assessment
 Survey
", "
description
": "
A
 comprehensive
 survey
 to
 assess
 your
 organization
's
 cybersecurity
 posture
 and
 identify
 areas
 for
 improvement
.", "
questions
": [ { "
id
": "
cyber_001
", "
text
": "
What
 is
 the
 size
 of
 your
 organization
?", "
type
": "
single_choice
", "
options
": [ { "
value
": "
small
", "
label
": "
Small
 (1-50
 employees
)" }, { "
value
": "
medium
", "
label
": "
Medium
 (51-500
 employees
)" }, { "
value
": "
large
", "
label
": "
Large
 (501+
 employees
)" } ] }, { "
id
": "
cyber_002
", "
text
": "
Does
 your
 organization
 have
 a
 dedicated
 IT
 security
 team
?", "
type
": "
yes_no
", "
options
": [ { "
value
": "
yes
", "
label
": "
Yes
" }, { "
value
": "
no
", "
label
": "
No
" } ] }, { "
id
": "
cyber_003
", "
text
": "
How
 often
 does
 your
 organization
 conduct
 security
 awareness
 training
?", "
type
": "
single_choice
", "
options
": [ { "
value
": "
never
", "
label
": "
Never
" }, { "
value
": "
annually
", "
label
": "
Annually
" }, { "
value
": "
quarterly
", "
label
": "
Quarterly
" }, { "
value
": "
monthly
", "
label
": "
Monthly
" } ] }, { "
id
": "
cyber_004
", "
text
": "
What
 type
 of
 antivirus
 solution
 does
 your
 organization
 use
?", "
type
": "
single_choice
", "
options
": [ { "
value
": "
none
", "
label
": "
No
 antivirus
 solution
" }, { "
value
": "
basic
", "
label
": "
Basic
 free
 antivirus
" }, { "
value
": "
commercial
", "
label
": "
Commercial
 antivirus
 suite
" }, { "
value
": "
enterprise
", "
label
": "
Enterprise
 security
 platform
" } ] }, { "
id
": "
cyber_005
", "
text
": "
Does
 your
 organization
 have
 a
 written
 cybersecurity
 policy
?", "
type
": "
yes_no
", "
options
": [ { "
value
": "
yes
", "
label
": "
Yes
" }, { "
value
": "
no
", "
label
": "
No
" } ] }, { "
id
": "
cyber_006
", "
text
": "
How
 often
 does
 your
 organization
 backup
 critical
 data
?", "
type
": "
single_choice
", "
options
": [ { "
value
": "
never
", "
label
": "
Never
" }, { "
value
": "
rarely
", "
label
": "
Rarely
" }, { "
value
": "
monthly
", "
label
": "
Monthly
" }, { "
value
": "
weekly
", "
label
": "
Weekly
" }, { "
value
": "
daily
", "
label
": "
Daily
" } ] }, { "
id
": "
cyber_007
", "
text
": "
Does
 your
 organization
 use
 multi-factor
 authentication
 (MFA)
?", "
type
": "
single_choice
", "
options
": [ { "
value
": "
never
", "
label
": "
Never
" }, { "
value
": "
some_systems
", "
label
": "
For
 some
 systems
" }, { "
value
": "
most_systems
", "
label
": "
For
 most
 systems
" }, { "
value
": "
all_systems
", "
label
": "
For
 all
 systems
" } ] }, { "
id
": "
cyber_008
", "
text
": "
How
 does
 your
 organization
 handle
 software
 updates
 and
 patches
?", "
type
": "
single_choice
", "
options
": [ { "
value
": "
manual
", "
label
": "
Manual
 updates
 as
 needed
" }, { "
value
": "
scheduled
", "
label
": "
Scheduled
 regular
 updates
" }, { "
value
": "
automatic
", "
label
": "
Automatic
 updates
 enabled
" } ] }, { "
id
": "
cyber_009
", "
text
": "
Has
 your
 organization
 experienced
 a
 cybersecurity
 incident
 in
 the
 past
 year
?", "
type
": "
yes_no
", "
options
": [ { "
value
": "
yes
", "
label
": "
Yes
" }, { "
value
": "
no
", "
label
": "
No
" } ] }, { "
id
": "
cyber_010
", "
text
": "
Does
 your
 organization
 have
 a
 disaster
 recovery
 plan
?", "
type
": "
yes_no
", "
options
": [ { "
value
": "
yes
", "
label
": "
Yes
" }, { "
value
": "
no
", "
label
": "
No
" } ] }, { "
id
": "
cyber_011
", "
text
": "
How
 does
 your
 organization
 monitor
 network
 security
?", "
type
": "
single_choice
", "
options
": [ { "
value
": "
none
", "
label
": "
No
 monitoring
" }, { "
value
": "
basic
", "
label
": "
Basic
 monitoring
 tools
" }, { "
value
": "
advanced
", "
label
": "
Advanced
 monitoring
 and
 analytics
" } ] }, { "
id
": "
cyber_012
", "
text
": "
What
 is
 your
 organization
's
 approach
 to
 employee
 access
 control
?", "
type
": "
single_choice
", "
options
": [ { "
value
": "
open
", "
label
": "
Open
 access
 to
 most
 systems
" }, { "
value
": "
role_based
", "
label
": "
Role-based
 access
 control
" }, { "
value
": "
strict
", "
label
": "
Strict
 least-privilege
 access
" } ] }, { "
id
": "
cyber_013
", "
text
": "
Does
 your
 organization
 conduct
 regular
 security
 audits
?", "
type
": "
single_choice
", "
options
": [ { "
value
": "
never
", "
label
": "
Never
" }, { "
value
": "
rarely
", "
label
": "
Rarely
" }, { "
value
": "
annually
", "
label
": "
Annually
" }, { "
value
": "
quarterly
", "
label
": "
Quarterly
" } ] }, { "
id
": "
cyber_014
", "
text
": "
How
 does
 your
 organization
 secure
 sensitive
 data
?", "
type
": "
multiple_choice
", "
options
": [ { "
value
": "
encryption
", "
label
": "
Data
 encryption
" }, { "
value
": "
access_controls
", "
label
": "
Access
 controls
" }, { "
value
": "
secure_storage
", "
label
": "
Secure
 storage
 solutions
" }, { "
value
": "
none
", "
label
": "
No
 specific
 measures
" } ] }, { "
id
": "
cyber_015
", "
text
": "
What
 is
 the
 biggest
 cybersecurity
 challenge
 your
 organization
 faces
?", "
type
": "
single_choice
", "
options
": [ { "
value
": "
budget
", "
label
": "
Limited
 budget
" }, { "
value
": "
expertise
", "
label
": "
Lack
 of
 expertise
" }, { "
value
": "
awareness
", "
label
": "
Employee
 awareness
" }, { "
value
": "
technology
", "
label
": "
Outdated
 technology
" }, { "
value
": "
compliance
", "
label
": "
Compliance
 requirements
" } ] } ] }'''

    print("=== USER SAMPLE TEST ===")
    print(f"Original length: {len(user_sample)}")

    try:
        sanitized = service._sanitize_raw_output(user_sample)
        print(f"Sanitized length: {len(sanitized)}")

        parsed = json.loads(sanitized)
        print(f"✅ Parsed successfully!")
        print(f"📊 Questions found: {len(parsed.get('questions', []))}")

        # Print first few question IDs to verify
        questions = parsed.get('questions', [])
        for i, q in enumerate(questions[:5]):
            print(f"  Question {i+1}: {q.get('id', 'no-id')} - {q.get('text', 'no-text')[:50]}...")

        print(f"✅ SUCCESS: Parsed {len(questions)} questions (vs previous 2)")
        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_user_exact_sample()