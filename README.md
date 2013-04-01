<a name="top"></a>Open Competencies
===

Sections
---
- [Vision](#vision)
- [Use cases](#use_cases)
- [Other problems addressed by open competencies](#other_problems)
- [Outline of structure - current thinking](#structure_outline)
- [Outline of dynamic aspects](#dynamic_outline)
- [Comparison to existing offerings](#comparison_existing)
- [Open Competencies is not...](#is_not)
- [Pre-coding decisions](#pre_coding_decisions)

<a name="vision"></a>Vision
-------
Open Competencies is a dynamic list of all the information you could learn.  It is a tree of knowledge, with different relationships identified between all of the bits of knowledge.

How do you use it?  Let's say you want to be a professional programmer.  You click a button, and all of the bits of knowledge needed to be a programmer light up.  You realize you don't just want to be a programmer.  You  also want to write really well, not just about technical topics.  So you click a few buttons that describes how you want to use writing in your life.  All of the bits that relate to writing well light up.

A separate tool will let you take a copy of your learning targets, and track your progress in learning them.  That needs to be a separate tool, because it requires a different kind of security model.

[top](#top)

<a name="use_cases"></a>Use Cases
---------
- You are a school that wants to implement competency education.  You interview new students as they come into your school.  You make a map of what each student needs to learn during their time in high school.  When they finish their map, they graduate from high school.
- You are a parent.  You use Open Competencies to help your child figure out what to focus on in their learning.
- You are a recent college graduate.  No one is telling you what to focus on anymore.  You use Open Competencies to lay out your lifelong learning goals.

[top](#top)

<a name="other_problems"></a>Other problems addressed by Open Competencies
---
Programmers have been using vim and emacs to make their work more efficient since the 1970's, while most teachers are still using Word to write curriculum.  This makes the education world about 40 years behind the open source programming world in terms of efficiency.  This project will bring some of the workflow efficiency of the open source world into the realm of professional educators:
- Forking:  Any school can fork any other schools set of pathways through the learning targets.  It should be possible, actually, to fork the entire set of learning targets itself.
- Continuous Revision:  Education standards are typically created by a small group of educators working for a specified time period.  Whatever they create stands until they can get together again to revise their work.  Open Competencies allows for continuous revision of the entire set of learning targets.

[top](#top)

<a name="structure_outline"></a>Outline of structure - current thinking
---
The inspiration for this project comes from working within a fairly traditional model of structuring knowledge, by academic subject areas.  The thinking so far has been to lay out knowledge in a hierarchy like this:
- [Subject Area](https://github.com/openlearningtools/opencompetencies/blob/master/GLOSSARY.md#subject)
    - [Subdiscipline Area](https://github.com/openlearningtools/opencompetencies/blob/master/GLOSSARY.md#subdiscipline_area)
        - [Competency Area](https://github.com/openlearningtools/opencompetencies/blob/master/GLOSSARY.md#competency_area)
            - This may be an appropriate place to describe what each of the four [performance levels](https://github.com/openlearningtools/opencompetencies/blob/master/GLOSSARY.md#performance_level) look like in this particular comptency area.
            - [Essential Understanding](https://github.com/openlearningtools/opencompetencies/blob/master/GLOSSARY.md#essential_understanding)
                - [Learning Target](https://github.com/openlearningtools/opencompetencies/blob/master/GLOSSARY.md#learning_target)

For example:
- Science
    - Physical Science
        - Motion and Forces
            - A description of what it looks like to work at the [apprentice](https://github.com/openlearningtools/opencompetencies/blob/master/GLOSSARY.md#apprentice), [technician](https://github.com/openlearningtools/opencompetencies/blob/master/GLOSSARY.md#technician), [master](https://github.com/openlearningtools/opencompetencies/blob/master/GLOSSARY.md#master), and [professional](https://github.com/openlearningtools/opencompetencies/blob/master/GLOSSARY.md#professional) levels in this particular competency area.
            - Understand that the motion of everyday objects is governed by Newton's three laws.
                - Understand Newton's first law.

We can see that this hierarchy does not go very deep.  Some subjects will need greater depths than others.  It seems to be worth naming the first few levels specifically, but at some point it seems appropriate to simply allow further nesting of "learning targets".

[top](#top)

<a name="dynamic_outline"></a>Outline of dynamic aspects
---
There are several things we need to be able to do with the data:
- Connect prerequisite knowledge.
    - This is probably the most important feature, because this will support the rapid identification of learning paths.  Click on a low-level learning target, and all of the branches above it light up, but also many parallel branches that are required to fully understand a learning target in the context of a profession.
- Connect knowledge that is related in a variety of ways.
    - Knowledge that is required for a profession.
    - Knowledge that is recommended for a profession.
    - Knowledge that a person is interested in, for nonprofessional reasons.

[top](#top)

<a name="comparison_existing"></a>Comparison to existing offerings
---
Most existing sets of educational standards are static sets, produced by teams of teachers and content-area experts:
- [Common Core State Standards](http://www.corestandards.org/) Aims to be a set of standards that every state in the country adopts.  Currently covers Mathematics and English Language Arts.
- [California State Standards](http://www.cde.ca.gov/be/st/ss/) California's standards consistently [rank high](http://standards.educationgadfly.net/) on the Fordham Institute's evaluation of state standards.
- For comparison, [Alaska's standards (pdf)](http://www.eed.state.ak.us/standards/pdf/standards.pdf) consistently rank extremely poorly.

[top](#top)

<a name="is_not"></a>Open Competencies is not...
---
It is important to understand what problems Open Competencies does not solve, because we will think about these problems as we are designing the tool.  It is important to understand what is outside the scope of Open Competencies, but also how that problem is to be addressed.

Open Competencies is not:
- A way to assess an individual's competence.  The Open Curriculum Builder can be used to build assessments based on competencies.
- A way to track an individual's progress through their targeted competencies.  The Open Learning Tracker can be used for this purpose.
- A curriculum, or a body of knowledge.  The Open Curriculum Builder can be used to design curriculum, or to map out a set of resources that can be used to learn a desired set of competencies.  Open Competencies is just a set of targets for your learning.

[top](#top)

<a name="pre_coding_decisions"></a>Pre-coding decisions
---
A number of decisions need to be made before we write any code:
- Agree on the overall scope of this project, as laid out in the [Vision](#vision) and [Use Cases](#use_cases) sections.
- Write any more functional specs needed before coding.
- Agree on a taxonomy for the hierarchy of learning targets.
- Agree on an overall approach to identifying the kinds of relationships between different pieces of knowledge?
- [(done)](https://github.com/openlearningtools/opencompetencies/blob/master/GLOSSARY.md) Write a glossary for the first few levels in the taxonomy
- Move much of this file to a wiki. Readme is mostly technical, and links to the wiki.
- Agree on which framework to use

[top](#top)
