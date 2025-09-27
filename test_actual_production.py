#!/usr/bin/env python3
"""
Test with the EXACT production sample the user provided
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.generation_service import GenerationService
from unittest.mock import MagicMock
import json

def test_exact_production_sample():
    """Test with user's exact production sample that was sanitized but still has spacing issues"""

    mock_db = MagicMock()
    service = GenerationService(mock_db)

    # This is the EXACT sanitized text from the user's production logs
    production_sanitized = """{


 "
title
":
 "
Enterprise
 Software
 Market
 Research
 Study
",


 "
description
":
 "
A
 comprehensive
 study
 to
 assess
 pricing
 sensitivity
,
 feature
 priorities
,
 brand
 perception
,
 and
 purchase
 intent
 for
 a
 new
 enterprise
 software
 product
 targeting
 general
 consumers
 and
 pros
umers
.",


 "
sections
":
 [


 {


 "
id
":

1
,


 "
title
":
 "
S
cre
ener
 &
 Dem
ographics
",


 "
description
":
 "
Initial
 screening
 questions
 and
 demographic
 information
",


 "
questions
":
 [


 {


 "
id
":
 "
q
1
",


 "
text
":
 "
What
 is
 your
 age
?",


 "
type
":
 "
multiple
_choice
",


 "
options
":
 ["
Under

18
",
 "
18
-
24
",
 "
25
-
34
",
 "
35
-
44
",
 "
45
-
54
",
 "
55
-
64
",
 "
65
 or
 older
"],


 "
required
":
 true
,


 "
method
ology
":
 "
screen
ing
",


 "
validation
":
 "
single
_select
;
 terminate
_if
:
Under

18
",


 "
order
":

1



 },


 {


 "
id
":
 "
q
2
",


 "
text
":
 "
Where
 do
 you
 currently
 reside
?",


 "
type
":
 "
multiple
_choice
",


 "
options
":
 ["
United
 States
",
 "
Canada
",
 "
United
 Kingdom
",
 "
European
 Union
",
 "
AP
AC
",
 "
LAT
AM
",
 "
Middle
 East
 &
 Africa
",
 "
Other
"],


 "
required
":
 true
,


 "
method
ology
":
 "
screen
ing
",


 "
validation
":
 "
single
_select
",


 "
order
":

2



 },


 {


 "
id
":
 "
q
3
",


 "
text
":
 "
Which
 of
 the
 following
 best
 describes
 your
 role
 in
 purchasing
 or
 subscribing
 to
 software
 tools
 for
 yourself
 or
 your
 household
?",


 "
type
":
 "
multiple
_choice
",


 "
options
":
 ["
I
 am
 the
 primary
 decision
-maker
",
 "
I
 share
 decision
-making
 with
 others
",
 "
I
 influence
 but
 do
 not
 decide
",
 "
I
 am
 not
 involved
 in
 software
 purchases
"],


 "
required
":
 true
,


 "
method
ology
":
 "
screen
ing
",


 "
validation
":
 "
single
_select
;
 terminate
_if
:I
 am
 not
 involved
 in
 software
 purchases
",


 "
order
":

3



 },


 {


 "
id
":
 "
q
4
",


 "
text
":
 "
Have
 you
 purchased
 or
 subscribed
 to
 any
 productivity
 or
 collaboration
 software
 (
e
.g
.,
 cloud
 storage
,
 project
 management
,
 note
-taking
,
 task
 apps
)
 in
 the
 last

12
 months
?",


 "
type
":
 "
multiple
_choice
",


 "
options
":
 ["
Yes
,
 paid
 subscription
",
 "
Yes
,
 free
 version
 only
",
 "
No
"],


 "
required
":
 true
,


 "
method
ology
":
 "
screen
ing
",


 "
validation
":
 "
single
_select
",


 "
order
":

4



 },


 {


 "
id
":
 "
q
5
",


 "
text
":
 "
What
 is
 your
 total
 annual
 household
 income
 before
 taxes
?",


 "
type
":
 "
multiple
_choice
",


 "
options
":
 ["
Under
 $
25
,
000
",
 "$
25
,
000
-$
49
,
999
",
 "$
50
,
000
-$
74
,
999
",
 "$
75
,
000
-$
99
,
999
",
 "$
100
,
000
-$
149
,
999
",
 "$
150
,
000
-$
199
,
999
",
 "$
200
,
000
 or
 more
",
 "
Prefer
 not
 to
 say
"],


 "
required
":
 true
,


 "
method
ology
":
 "
dem
ographics
",


 "
validation
":
 "
single
_select
",


 "
order
":

5



 },


 {


 "
id
":
 "
q
6
",


 "
text
":
 "
What
 is
 the
 highest
 level
 of
 education
 you
 have
 completed
?",


 "
type
":
 "
multiple
_choice
",


 "
options
":
 ["
High
 school
 or
 less
",
 "
Some
 college
/
Associate
",
 "
Bachelor
's
 degree
",
 "
Graduate
/
Professional
 degree
",
 "
Prefer
 not
 to
 say
"],


 "
required
":
 false
,


 "
method
ology
":
 "
dem
ographics
",


 "
validation
":
 "
single
_select
",


 "
order
":

6



 },


 {


 "
id
":
 "
q
7
",


 "
text
":
 "
Which
 best
 describes
 your
 current
 employment
 status
?",


 "
type
":
 "
multiple
_choice
",


 "
options
":
 ["
Full
-time
 employed
",
 "
Part
-time
 employed
",
 "
Self
-employed
",
 "
Student
",
 "
Hom
emaker
",
 "
Un
em
ployed
 looking
 for
 work
",
 "
Ret
ired
",
 "
Prefer
 not
 to
 say
"],


 "
required
":
 true
,


 "
method
ology
":
 "
dem
ographics
",


 "
validation
":
 "
single
_select
",


 "
order
":

7



 },


 {


 "
id
":
 "
q
8
",


 "
text
":
 "
Attention
 check
:
 Please
 select
 the
 option
 labeled
 '
I
 am
 paying
 attention
'.
",


 "
type
":
 "
multiple
_choice
",


 "
options
":
 ["
I
 am
 paying
 attention
",
 "
I
 am
 not
 paying
 attention
",
 "
Prefer
 not
 to
 answer
"],


 "
required
":
 true
,


 "
method
ology
":
 "
quality
_check
",


 "
validation
":
 "
single
_select
;
 terminate
_if
:I
 am
 not
 paying
 attention
",


 "
order
":

8



 }


 ]


 },


 {


 "
id
":

2
,


 "
title
":
 "
Consumer
 Details
",


 "
description
":
 "
Detailed
 consumer
 information
 and
 behavior
 patterns
",


 "
questions
":
 [


 {


 "
id
":
 "
q
9
",


 "
text
":
 "
Which
 devices
 do
 you
 use
 weekly
 for
 personal
 productivity
 or
 collaboration
?",


 "
type
":
 "
multiple
_select
",


 "
options
":
 ["
Windows
 PC
",
 "
Mac
",
 "
Linux
 PC
",
 "
Android
 phone
",
 "
i
Phone
",
 "
Tablet
",
 "
Other
"],


 "
required
":
 true
,


 "
method
ology
":
 "
behavior
",


 "
validation
":
 "
multi
_select
_min
1
",


 "
order
":

1



 },


 {


 "
id
":
 "
q
10
",


 "
text
":
 "
How
 many
 different
 software
 subscriptions
 do
 you
 currently
 pay
 for
 personally
?",


 "
type
":
 "
multiple
_choice
",


 "
options
":
 ["
None
",
 "
1
",
 "
2
",
 "
3
-
4
",
 "
5
 or
 more
"],


 "
required
":
 true
,


 "
method
ology
":
 "
behavior
",


 "
validation
":
 "
single
_select
",


 "
order
":

2



 },


 {


 "
id
":
 "
q
11
",


 "
text
":
 "
What
 are
 your
 primary
 reasons
 for
 subscribing
 to
 productivity
 or
 collaboration
 software
?",


 "
type
":
 "
multiple
_select
",


 "
options
":
 ["
Work
 or
 freelance
 projects
",
 "
Personal
 organization
 and
 tasks
",
 "
File
 storage
 and
 backup
",
 "
Team
 communication
",
 "
Learning
 and
 personal
 development
",
 "
Creative
 projects
",
 "
Other
"],


 "
required
":
 true
,


 "
method
ology
":
 "
behavior
",


 "
validation
":
 "
multi
_select
_min
1
",


 "
order
":

3



 },


 {


 "
id
":
 "
q
12
",


 "
text
":
 "
How
 important
 are
 the
 following
 when
 choosing
 a
 software
 subscription
?",


 "
type
":
 "
matrix
",


 "
options
":
 ["
Very
 un
important
",
 "
Un
important
",
 "
Neither
 important
 nor
 un
important
",
 "
Important
",
 "
Very
 important
"],


 "
required
":
 true
,


 "
method
ology
":
 "
att
itudes
",


 "
validation
":
 "
matrix
_single
_per
_row
;
 rows
:
Price
;
 rows
:
Ease
 of
 use
;
 rows
:
Security
 and
 privacy
;
 rows
:
Customer
 support
;
 rows
:
Integr
ations
;
 rows
:
Performance
 and
 reliability
",


 "
order
":

4



 },


 {


 "
id
":
 "
q
13
",


 "
text
":
 "
In
 a
 typical
 month
,
 about
 how
 much
 do
 you
 personally
 spend
 on
 software
 subscriptions
 for
 yourself
 (
not
 paid
 by
 employer
)?
",


 "
type
":
 "
multiple
_choice
",


 "
options
":
 ["
$
0
",
 "
Under
 $
10
",
 "$
10
-$
19
",
 "$
20
-$
29
",
 "$
30
-$
49
",
 "$
50
 or
 more
",
 "
Prefer
 not
 to
 say
"],


 "
required
":
 true
,


 "
method
ology
":
 "
behavior
",


 "
validation
":
 "
single
_select
",


 "
order
":

5



 }


 ]


 },


 {


 "
id
":

3
,


 "
title
":
 "
Consumer
 product
 awareness
,
 usage
 and
 preference
",


 "
description
":
 "
Understanding
 consumer
 awareness
,
 usage
 patterns
 and
 preferences
",


 "
questions
":
 [


 {


 "
id
":
 "
q
14
",


 "
text
":
 "
Which
 brands
 of
 productivity
 or
 collaboration
 software
 are
 you
 aware
 of
?",


 "
type
":
 "
multiple
_select
",


 "
options
":
 ["
Microsoft

365
",
 "
Google
 Workspace
",
 "
Dropbox
",
 "
Ever
note
",
 "
Not
ion
",
 "
As
ana
",
 "
T
rello
",
 "
Slack
",
 "
Box
",
 "
Apple
 i
Cloud
",
 "
Other
",
 "
None
 of
 the
 above
"],


 "
required
":
 true
,


 "
method
ology
":
 "
brand
_aw
areness
",


 "
validation
":
 "
multi
_select
_min
1
",


 "
order
":

1



 },


 {


 "
id
":
 "
q
15
",


 "
text
":
 "
Which
 of
 these
 have
 you
 used
 in
 the
 past

6
 months
?",


 "
type
":
 "
multiple
_select
",


 "
options
":
 ["
Microsoft

365
",
 "
Google
 Workspace
",
 "
Dropbox
",
 "
Ever
note
",
 "
Not
ion
",
 "
As
ana
",
 "
T
rello
",
 "
Slack
",
 "
Box
",
 "
Apple
 i
Cloud
",
 "
Other
",
 "
None
 of
 the
 above
"],


 "
required
":
 true
,


 "
method
ology
":
 "
usage
",


 "
validation
":
 "
multi
_select
_min
1
",


 "
order
":

2



 },


 {


 "
id
":
 "
q
16
",


 "
text
":
 "
Thinking
 about
 your
 primary
 productivity
 or
 collaboration
 software
,
 how
 satisfied
 are
 you
 overall
?",


 "
type
":
 "
scale
",


 "
options
":
 ["
Very
 dissatisfied
",
 "
D
iss
atisfied
",
 "
Neutral
",
 "
Satisfied
",
 "
Very
 satisfied
"],


 "
required
":
 true
,


 "
method
ology
":
 "
s
atisfaction
",


 "
validation
":
 "
single
_select
",


 "
order
":

3



 },


 {


 "
id
":
 "
q
17
",


 "
text
":
 "
How
 likely
 are
 you
 to
 recommend
 your
 primary
 productivity
 or
 collaboration
 software
 to
 a
 friend
 or
 colleague
?",


 "
type
":
 "
number
",


 "
options
":
 [],


 "
required
":
 true
,


 "
method
ology
":
 "
n
ps
",


 "
validation
":
 "
integer
_min
0
_max
10
",


 "
order
":

4



 },


 {


 "
id
":
 "
q
18
",


 "
text
":
 "
When
 choosing
 between
 similar
 software
 products
,
 which
 factor
 is
 most
 important
 to
 you
?",


 "
type
":
 "
multiple
_choice
",


 "
options
":
 ["
Lowest
 price
",
 "
Best
 features
",
 "
Ease
 of
 use
",
 "
Brand
 reputation
",
 "
Security
 and
 privacy
",
 "
Customer
 support
"],


 "
required
":
 true
,


 "
method
ology
":
 "
pre
ference
",


 "
validation
":
 "
single
_select
",


 "
order
":

5



 }


 ]


 },


 {


 "
id
":

4
,


 "
title
":
 "
Product
 introduction
 and
 Concept
 reaction
",


 "
description
":
 "
New
 product
 concept
 evaluation
,
 pricing
 sensitivity
,
 and
 purchase
 intent
",


 "
questions
":
 [


 {


 "
id
":
 "
q
19
",


 "
text
":
 "
Concept
 description
:
 Imagine
 a
 new
 cloud
-based
 productivity
 suite
 that
 combines
 notes
,
 tasks
,
 file
 storage
,
 real
-time
 collaboration
,
 and
 AI
-assisted
 summaries
 in
 one
 secure
 app
 with
 cross
-platform
 support
 and
 offline
 mode
.",


 "
type
":
 "
instruction
",


 "
options
":
 [],


 "
required
":
 false
,


 "
method
ology
":
 "
concept
_intro
",


 "
validation
":
 "
none
",


 "
order
":

1



 },


 {


 "
id
":
 "
q
20
",


 "
text
":
 "
How
 clear
 is
 the
 product
 concept
 you
 just
 read
?",


 "
type
":
 "
scale
",


 "
options
":
 ["
Not
 at
 all
 clear
",
 "
S
light
ly
 clear
",
 "
Moder
ately
 clear
",
 "
Very
 clear
",
 "
Ext
remely
 clear
"],


 "
required
":
 true
,


 "
method
ology
":
 "
concept
_cl
arity
",


 "
validation
":
 "
single
_select
",


 "
order
":

2



 },


 {


 "
id
":
 "
q
21
",


 "
text
":
 "
How
 likely
 would
 you
 be
 to
 try
 this
 product
 if
 available
 today
?",


 "
type
":
 "
scale
",


 "
options
":
 ["
Very
 unlikely
",
 "
Un
likely
",
 "
Neutral
",
 "
Lik
ely
",
 "
Very
 likely
"],


 "
required
":
 true
,


 "
method
ology
":
 "
purchase
_int
ent
",


 "
validation
":
 "
single
_select
",


 "
order
":

3



 },


 {


 "
id
":
 "
q
22
",


 "
text
":
 "
Which
 aspects
 of
 the
 concept
 are
 most
 appealing
 to
 you
?",


 "
type
":
 "
multiple
_select
",


 "
options
":
 ["
All
-in
-one
 integration
",
 "
AI
-assisted
 summaries
",
 "
Security
 and
 privacy
",
 "
Offline
 mode
",
 "
Cross
-platform
 support
",
 "
Real
-time
 collaboration
",
 "
Ease
 of
 use
",
 "
None
 of
 the
 above
"],


 "
required
":
 true
,


 "
method
ology
":
 "
concept
_re
action
",


 "
validation
":
 "
multi
_select
_min
1
",


 "
order
":

4



 },


 {


 "
id
":
 "
q
23
",


 "
text
":
 "
At
 what
 price
 would
 this
 product
 be
 so
 expensive
 that
 you
 would
 not
 consider
 buying
 it
?
 (
Too
 Exp
ensive
)",


 "
type
":
 "
number
",


 "
options
":
 [],


 "
required
":
 true
,


 "
method
ology
":
 "
van
_w
est
endor
p
",


 "
validation
":
 "
currency
_us
d
;
 integer
_or
_decimal
_min
0
;
 vw
_label
:
too
_exp
ensive
",


 "
order
":

5



 },


 {


 "
id
":
 "
q
24
",


 "
text
":
 "
At
 what
 price
 would
 you
 consider
 this
 product
 to
 be
 priced
 so
 low
 that
 you
 would
 feel
 the
 quality
 could
 not
 be
 very
 good
?
 (
Too
 Cheap
)",


 "
type
":
 "
number
",


 "
options
":
 [],


 "
required
":
 true
,


 "
method
ology
":
 "
van
_w
est
endor
p
",


 "
validation
":
 "
currency
_us
d
;
 integer
_or
_decimal
_min
0
;
 vw
_label
:
too
_
cheap
",


 "
order
":

6



 },


 {


 "
id
":
 "
q
25
",


 "
text
":
 "
At
 what
 price
 would
 you
 consider
 this
 product
 starting
 to
 get
 expensive
,
 so
 that
 it
 is
 not
 out
 of
 the
 question
,
 but
 you
 would
 have
 to
 give
 some
 thought
 to
 buying
 it
?
 (
Getting
 Exp
ensive
)",


 "
type
":
 "
number
",


 "
options
":
 [],


 "
required
":
 true
,


 "
method
ology
":
 "
van
_w
est
endor
p
",


 "
validation
":
 "
currency
_us
d
;
 integer
_or
_decimal
_min
0
;
 vw
_label
:get
ting
_exp
ensive
",


 "
order
":

7



 },


 {


 "
id
":
 "
q
26
",


 "
text
":
 "
At
 what
 price
 would
 you
 consider
 the
 product
 to
 be
 a
 bargain
,
 a
 great
 buy
 for
 the
 money
?
 (
Cheap
/
Good
 Value
)",


 "
type
":
 "
number
",


 "
options
":
 [],


 "
required
":
 true
,


 "
method
ology
":
 "
van
_w
est
endor
p
",


 "
validation
":
 "
currency
_us
d
;
 integer
_or
_decimal
_min
0
;
 vw
_label
:
cheap
_good
_value
",


 "
order
":

8



 },


 {


 "
id
":
 "
q
27
",


 "
text
":
 "
Please
 briefly
 explain
 the
 reasoning
 behind
 the
 price
 points
 you
 entered
 above
.",


 "
type
":
 "
open
_
ended
",


 "
options
":
 [],


 "
required
":
 true
,


 "
method
ology
":
 "
van
_w
est
endor
p
_follow
up
",


 "
validation
":
 "
min
_chars
:
20
",


 "
order
":

9



 },


 {


 "
id
":
 "
q
28
",


 "
text
":
 "
Max
Diff
:
 Of
 the
 following
 features
,
 which
 is
 Most
 Important
 and
 which
 is
 Least
 Important
 when
 deciding
 to
 subscribe
?",


 "
type
":
 "
max
diff
",


 "
options
":
 ["
Advanced
 AI
 summar
ization
",
 "
End
-to
-end
 encryption
",
 "
Unlimited
 file
 storage
",
 "
Offline
 access
",
 "
Real
-time
 collaboration
",
 "
Third
-party
 integrations
",
 "
Priority
 customer
 support
",
 "
Custom
izable
 workflows
"],


 "
required
":
 true
,


 "
method
ology
":
 "
max
diff
",


 "
validation
":
 "
md
_design
:
balanced
_blocks
_
8
_items
_
6
_tasks
_
3
_items
_per
_task
;
 include
_none
:false
",


 "
order
":

10



 },


 {


 "
id
":
 "
q
29
",


 "
text
":
 "
Con
joint
 Choice
 Task

1
:
 Which
 version
 would
 you
 choose
?",


 "
type
":
 "
choice
",


 "
options
":
 [


 "
Option
 A
 |
 Price
:
 $
6
.
99
/month
 |
 Storage
:

200
GB
 |
 Security
:
 Standard
 encryption
 |
 Support
:
 Email
 |
 AI
:
 Basic
 |
 Integr
ations
:
 Limited
",


 "
Option
 B
 |
 Price
:
 $
9
.
99
/month
 |
 Storage
:

1
TB
 |
 Security
:
 Enhanced
 encryption
 |
 Support
:
 Chat
 |
 AI
:
 Advanced
 |
 Integr
ations
:
 Popular
 apps
",


 "
Option
 C
 |
 Price
:
 $
14
.
99
/month
 |
 Storage
:

2
TB
 |
 Security
:
 Enterprise
-grade
 encryption
 |
 Support
:
 Phone
 |
 AI
:
 Advanced
 +
 Automation
 |
 Integr
ations
:
 Extensive
",


 "
None
 of
 these
"


 ],


 "
required
":
 true
,


 "
method
ology
":
 "
con
joint
_c
bc
",


 "
validation
":
 "
single
_select
_in
cludes
_none
;
 balanced
_attributes
:true
;
 orth
ogonal
_design
:true
;
 realistic
_levels
:true
",


 "
order
":

11



 },


 {


 "
id
":
 "
q
30
",


 "
text
":
 "
Con
joint
 Choice
 Task

2
:
 Which
 version
 would
 you
 choose
?",


 "
type
":
 "
choice
",


 "
options
":
 [


 "
Option
 A
 |
 Price
:
 $
4
.
99
/month
 |
 Storage
:

200
GB
 |
 Security
:
 Enhanced
 encryption
 |
 Support
:
 Email
 |
 AI
:
 None
 |
 Integr
ations
:
 Limited
",


 "
Option
 B
 |
 Price
:
 $
12
.
99
/month
 |
 Storage
:

1
TB
 |
 Security
:
 Enterprise
-grade
 encryption
 |
 Support
:
 Chat
 |
 AI
:
 Advanced
 |
 Integr
ations
:
 Popular
 apps
",


 "
Option
 C
 |
 Price
:
 $
9
.
99
/month
 |
 Storage
:

2
TB
 |
 Security
:
 Standard
 encryption
 |
 Support
:
 Phone
 |
 AI
:
 Basic
 |
 Integr
ations
:
 Extensive
",


 "
None
 of
 these
"


 ],


 "
required
":
 true
,


 "
method
ology
":
 "
con
joint
_c
bc
",


 "
validation
":
 "
single
_select
_in
cludes
_none
;
 balanced
_attributes
:true
;
 orth
ogonal
_design
:true
;
 realistic
_levels
:true
",


 "
order
":

12



 },


 {


 "
id
":
 "
q
31
",


 "
text
":
 "
Con
joint
 Choice
 Task

3
:
 Which
 version
 would
 you
 choose
?",


 "
type
":
 "
choice
",


 "
options
":
 [


 "
Option
 A
 |
 Price
:
 $
9
.
99
/month
 |
 Storage
:

200
GB
 |
 Security
:
 Enterprise
-grade
 encryption
 |
 Support
:
 Chat
 |
 AI
:
 Basic
 |
 Integr
ations
:
 Popular
 apps
",


 "
Option
 B
 |
 Price
:
 $
6
.
99
/month
 |
 Storage
:

1
TB
 |
 Security
:
 Standard
 encryption
 |
 Support
:
 Phone
 |
 AI
:
 None
 |
 Integr
ations
:
 Limited
",


 "
Option
 C
 |
 Price
:
 $
14
.
99
/month
 |
 Storage
:

2
TB
 |
 Security
:
 Enhanced
 encryption
 |
 Support
:
 Email
 |
 AI
:
 Advanced
 +
 Automation
 |
 Integr
ations
:
 Extensive
",


 "
None
 of
 these
"


 ],


 "
required
":
 true
,


 "
method
ology
":
 "
con
joint
_c
bc
",


 "
validation
":
 "
single
_select
_in
cludes
_none
;
 balanced
_attributes
:true
;
 orth
ogonal
_design
:true
;
 realistic
_levels
:true
",


 "
order
":

13



 },


 {


 "
id
":
 "
q
32
",


 "
text
":
 "
How
 likely
 would
 you
 be
 to
 subscribe
 at
 $
9
.
99
 per
 month
 for
 the
 concept
 described
?",


 "
type
":
 "
scale
",


 "
options
":
 ["
Definitely
 would
 not
 subscribe
",
 "
Probably
 would
 not
 subscribe
",
 "
M
ight
 or
 might
 not
 subscribe
",
 "
Probably
 would
 subscribe
",
 "
Definitely
 would
 subscribe
"],


 "
required
":
 true
,


 "
method
ology
":
 "
price
_point
_validation
",


 "
validation
":
 "
single
_select
",


 "
order
":

14



 }


 ]


 },


 {


 "
id
":

5
,


 "
title
":
 "
Method
ology
",


 "
description
":
 "
Method
ology
-specific
 questions
,
 validation
,
 and
 survey
 experience
",


 "
questions
":
 [


 {


 "
id
":
 "
q
33
",


 "
text
":
 "
Please
 indicate
 your
 agreement
:
 I
 answered
 the
 questions
 honestly
 and
 to
 the
 best
 of
 my
 ability
.",


 "
type
":
 "
scale
",


 "
options
":
 ["
Strong
ly
 disagree
",
 "
Dis
agree
",
 "
Neither
 agree
 nor
 disagree
",
 "
Agree
",
 "
Strong
ly
 agree
"],


 "
required
":
 true
,


 "
method
ology
":
 "
quality
_check
",


 "
validation
":
 "
single
_select
",


 "
order
":

1



 },


 {


 "
id
":
 "
q
34
",


 "
text
":
 "
How
 easy
 or
 difficult
 was
 this
 survey
 to
 complete
 on
 your
 device
?",


 "
type
":
 "
scale
",


 "
options
":
 ["
Very
 difficult
",
 "
D
ifficult
",
 "
Neither
 easy
 nor
 difficult
",
 "
Easy
",
 "
Very
 easy
"],


 "
required
":
 false
,


 "
method
ology
":
 "
deployment
_feedback
",


 "
validation
":
 "
single
_select
",


 "
order
":

2



 },


 {


 "
id
":
 "
q
35
",


 "
text
":
 "
Do
 you
 have
 any
 feedback
 to
 improve
 the
 clarity
 of
 the
 concept
 or
 the
 questions
?",


 "
type
":
 "
open
_
ended
",


 "
options
":
 [],


 "
required
":
 false
,


 "
method
ology
":
 "
survey
_feedback
",


 "
validation
":
 "
max
_chars
:
500
",


 "
order
":

3



 },


 {


 "
id
":
 "
q
36
",


 "
text
":
 "
Consistency
 check
:
 Earlier
 you
 indicated
 how
 many
 subscriptions
 you
 pay
 for
;
 approximately
 how
 many
 different
 software
 tools
 do
 you
 actively
 use
 weekly
?",


 "
type
":
 "
multiple
_choice
",


 "
options
":
 ["
0
",
 "
1
",
 "
2
",
 "
3
-
4
",
 "
5
-
6
",
 "
7
 or
 more
"],


 "
required
":
 true
,


 "
method
ology
":
 "
quality
_check
",


 "
validation
":
 "
single
_select
;
 soft
_check
_with
:q
10
",


 "
order
":

4



 },


 {


 "
id
":
 "
q
37
",


 "
text
":
 "
What
 is
 your
 gender
?",


 "
type
":
 "
multiple
_choice
",


 "
options
":
 ["
Female
",
 "
Male
",
 "
Non
-b
inary
",
 "
Prefer
 to
 self
-des
cribe
",
 "
Prefer
 not
 to
 say
"],


 "
required
":
 false
,


 "
method
ology
":
 "
dem
ographics
",


 "
validation
":
 "
single
_select
",


 "
order
":

5



 },


 {


 "
id
":
 "
q
38
",


 "
text
":
 "
Please
 select
 the
 word
 that
 best
 completes
 this
 sequence
:
 Apple
,
 Banana
,
 Cherry
,
 ____
 (
choose
 '
Date
').
",


 "
type
":
 "
multiple
_choice
",


 "
options
":
 ["
Car
rot
",
 "
Date
",
 "
Egg
plant
",
 "
Fig
"],


 "
required
":
 true
,


 "
method
ology
":
 "
attention
_check
",


 "
validation
":
 "
single
_select
;
 correct
_answer
:
Date
",


 "
order
":

6



 }


 ]


 }


 ],


 "
metadata
":
 {


 "
estimated
_time
":

14
,


 "
method
ology
_tags
":
 ["
van
_w
est
endor
p
",
 "
con
joint
_c
bc
",
 "
max
diff
",
 "
pricing
_re
search
",
 "
brand
_aw
areness
",
 "
purchase
_int
ent
",
 "
n
ps
"],


 "
target
_res
ponses
":

600
,


 "
quality
_score
":

0
.
93
,


 "
sections
_count
":

5
,


 "
sample
_size
_guid
ance
":
 "
For
 CBC
 with

6
-
9
 tasks
 and

3
 alternatives
 per
 task
,
 target
 at
 least

400
 completes
 for
 stable
 utilities
;
 for
 Max
Diff
 with

8
 items
 and

6
 tasks
,

300
-
500
 completes
 recommended
;
 for
 Van
 West
endor
p
,

200
+
 completes
 recommended
 for
 stable
 intersection
 estimates
.",


 "
cbc
_attributes
":
 ["
Price
:
 $
4
.
99
,
 $
6
.
99
,
 $
9
.
99
,
 $
12
.
99
,
 $
14
.
99
 per
 month
",
 "
Storage
:

200
GB
,

1
TB
,

2
TB
",
 "
Security
:
 Standard
 encryption
,
 Enhanced
 encryption
,
 Enterprise
-grade
 encryption
",
 "
Support
:
 Email
,
 Chat
,
 Phone
",
 "
AI
:
 None
,
 Basic
,
 Advanced
,
 Advanced
 +
 Automation
",
 "
Integr
ations
:
 Limited
,
 Popular
 apps
,
 Extensive
"],


 "
max
diff
_design
":
 "
Balanced
 choice
 sets
 with
 each
 item
 appearing
 an
 equal
 number
 of
 times
 and
 paired
 frequency
 balanced
;

6
 tasks
 of

3
 items
 per
 task
 per
 respondent
;
 no
 '
None
'
 option
.",


 "
vw
_require
ments
":
 "
Exactly

4
 Van
 West
endor
p
 questions
 included
 with
 logical
 price
 formatting
 in
 USD
 and
 open
-ended
 reasoning
 follow
-up
.",


 "
privacy
":
 "
Responses
 are
 confidential
 and
 will
 be
 analyzed
 in
 aggregate
 only
.",


 "
device
_
compat
ibility
":
 "
Survey
 optimized
 for
 mobile
 and
 desktop
;
 single
-column
 layout
 with
 tap
-friendly
 options
.",


 "
pilot
_test
":
 "
Run
 a

20
-
30
 respondent
 soft
 launch
 to
 validate
 timing
,
 comprehension
,
 and
 pricing
 input
 distributions
 before
 full
 field
."


 }

}"""

    print("=== EXACT PRODUCTION SAMPLE TEST ===")
    print(f"Input length: {len(production_sanitized)} characters")
    print("This is the EXACT sanitized text from production logs with spacing issues")

    try:
        # Test the complete extraction pipeline
        result = service._extract_survey_json(production_sanitized)

        if result:
            print(f"✅ Full extraction successful!")
            if 'sections' in result:
                total_questions = sum(len(section.get('questions', [])) for section in result.get('sections', []))
                print(f"✅ Extracted {total_questions} questions from {len(result['sections'])} sections")

                # Print section breakdown
                for i, section in enumerate(result['sections']):
                    section_questions = len(section.get('questions', []))
                    print(f"  Section {i+1}: {section_questions} questions")

                return total_questions
            else:
                print(f"⚠️ No sections found in result: {list(result.keys())}")
                return 0
        else:
            print(f"❌ Full extraction returned None")
            return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    questions_found = test_exact_production_sample()
    if questions_found >= 30:
        print(f"\n🎉 PERFECT SUCCESS: Extracted {questions_found} questions from production sample!")
        print("The 'questions disaster' is completely fixed!")
    elif questions_found > 10:
        print(f"\n✅ GOOD SUCCESS: Extracted {questions_found} questions (major improvement)!")
    elif questions_found > 0:
        print(f"\n⚠️ PARTIAL SUCCESS: Extracted {questions_found} questions (some improvement)")
    else:
        print(f"\n❌ FAILURE: No questions extracted")