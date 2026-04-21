# Estimation & Prioritization Framework

Software estimations are generally consistently wrong to some greater or lesser extent. Humans are [terrible at estimating how long something will take](https://www.linkedin.com/pulse/afraid-very-chris-creel/). Technology businesses, however, must run on predictable, productive cycles to make customers happy. This can create a massive conflict between the realities of writing software and the realities of running a successful business. So, how do you reconcile the disconnect between an inherently unpredictable activity (software development) and creating a great user experience based on predictable productivity?

*Data.*

If we can collect high-quality performance data, then we can measure our productivity. This, in turn, enables us to create forecasting models based on actual performance instead of desired performance. We can then have critical conversations about improving our velocity and predictability.

The methods below are our current approach to collecting high-quality data. These methods will change over time as we continue to strive to improve our predictive models. In summary, we attempt to estimate our future velocity by collecting high-integrity data on our past velocity. We based our estimates on two subjective opinions about a piece of work:

1. Risk – How predictable is this work?  
2. Intensity – How much time do we think it will take?

It doesn't matter if these end up being precisely correct or wildly incorrect. What matters is that we measure, identify the gaps, and learn. Said another way, it doesn't matter that person A is usually off by X or Y. It certainly matters that person A learns from their mistakes and improves the next time.

So it is critical that we collect all of this data so that we can then create predictive models that will help us forecast and measure our variability and then learn how to improve. This creates an 'experimental' culture where we are constantly measuring, stating a hypothesis about how we can improve, running an experiment, and then watching for results in the data.

Based on the determination of Risk and Intensity, we can then look up the resulting User Story Points in the following table:

### Estimation Table

|  | High Risk | Medium Risk | Low Risk | No Risk |
| :---: | :---: | :---: | :---: | :---: |
| High Intensity | 21 | 13 | 8 | 5 |
| Medium Intensity | 13 | 8 | 5 | 3 |
| Low Intensity | 8 | 5 | 3 | 2 |
| No Intensity | 5 | 3 | 2 | 1 |

Note that User Story Points are just a unit of measure. Think of it as the 'weight' of the story. For example, a story with 21 User Story Points weighs *a* *lot,* whereas a story with just one User Story Point is very light indeed.

In fact, as a general rule, we will not allow a story to transition to 'in progress' until the weight is five or less. Mentally, you can think about a boulder that you, as an individual, just can't move because it is too heavy. So when you encounter a story that weighs too much, the game becomes how to break it down into smaller pieces that you can move.

We define risk as the degree to which a piece of work might introduce unpredictability into our development efforts. We can reduce all varieties of development risk with an aggressive, comprehensive testing strategy. Unit testing, integration testing, and automated end-user testing are the most effective tools we have to keep our risks low and our ability to deliver on our development commitments predictable.

Note that it is essential that before putting an issue into progress, the risk should be set by the person who will do the work. Something that is low risk for one person might be high risk for another. The team should then always look to assign the issue to the person who perceives the lowest risk.

## High Risk

High-risk work could introduce a lot of unpredictability into the development process. High-risk work might:

1. Create ripple effects that impact others on the team  
2. Be difficult to undo once implemented and could cause more problems  
3. Increase the risk of other development efforts in unanticipated ways  
4. Take much longer than expected (e.g., greater than 50% or original estimate)  
5. Depends on a third party's part. This can be even more severe when they do not work for us.

### Examples of High-Risk Work

#### Doing something we've never done before

Sometimes, we need to introduce new technology, design concepts, or features with which we have no experience. This often leads to unexpected delays, gotchas, and technical debt because we may not know how to do it 'right' the first time. Ways to reduce the risk:

* Use a test-driven development approach by writing the tests first to help us better understand what the code should do before we worry about how the code will do it.  
* Break it into multiple pieces, one of which is to research the best way to do whatever it is we are about to do.  
* Hand the work off to someone else who has done it before or ask them to collaborate  
* Hire an outside partner who has a lot of experience solving the problem at hand

#### Writing a large amount of entirely new code

Writing a lot of new code opens up many opportunities for defects, poor documentation, and technical debt. Ways to reduce the risk:

* Create an issue to quickly create a throwaway prototype to learn how to do it and then another issue to create the production-ready solution  
* Solve a more minor problem that requires less code using an architecture that can be expanded to accommodate the more significant problem  
* Find established libraries that can address some of the commodity aspects of the problem at hand

#### Working on unfamiliar, confusing, poorly documented code with poor test coverage

Working on unfamiliar code that needs to be better documented and have low test coverage can lead to damaging side effects and an increase in bugs. Ways to reduce the risk:

* Break the work into two pieces:  
  * refactor away the confusing bits  
  * then address any documentation and test coverage issues  
* Wrap the confusing code with a high-integrity code that solves the problem. Add a TODO to address the underlying issues.  
* Get the original author to do the work and then have them work on improving the code after the problem is solved.

#### Changing architectures

Changing an architecture can often lead to side effects. Ways to reduce the risk:

* Look for opportunities to break the architecture apart into smaller micro-services that can be replaced with fewer side effects.  
* Build in parallel and then create a dynamic way to switch between the two solutions. This way, you can safely switch between the new and old architecture.  
* Establish the 'Definition of Victory', or DoV for the redesign. What will you achieve if you do it perfectly? Frequently you will find that the investment just isn't worth it.

#### Changing database tables

Changing database tables often leads to trouble. Parts of the code that expected tables in one way now can break because someone changed the tables. Ways to reduce the risk:

* One way to reduce the risk in this scenario is to use an ORM and never use the database directly.  
* Another way to do this is to replicate the data from the old tables to the new tables. Then, you can incrementally transition code from the old approach to the new approach.  
* Of course, you should always back up the data to quickly revert to the old approach if testing fails.

## Medium Risk

Medium-risk work could introduce some unpredictability into the development process. For example, a medium-risk work could:

1. Undoing the work will take effort but is straightforward  
2. It might take longer than expected but not dramatically so (e.g, less than 50% change)  
3. Others might be impacted, but the impact is well-understood, and everyone is prepared

### Examples of Medium Risk Work

#### Upgrading a dependency

Upgrading a dependency is often fraught with peril and surprisingly so. Fortunately, this can be done on a branch and with sufficient testing, the risk should be manageable. However, this work can still have unintended side-effects long after it was assumed that everything was working properly. Ways to reduce the risk:

* Good testing is the best way to reduce risk.  
* Always do this on a branch and do not push to the development or master branch without extensive testing  
* Research 'problem with version x.y.z' on the Internet to see if others have experienced problems with a new version.

#### Refactoring existing code

Refactoring existing code to, say, remove technical debt can often introduce bugs and anomalous behavior. Ways to reduce the risk:

* You can reduce this risk with a robust testing strategy. When refactoring, the behavior shouldn't change, just the implementation. So, all the tests should pass despite the change in the code.  
* Refactor in smaller steps over a more extended period instead of all in one go. Create an issue for each step.  
* Create an abstraction layer around the existing code and then use an abstract factory pattern to switch between an old and new implementation

#### Fixing a bug in a library

Whenever you are addressing a bug in a library there can be ripple effects into all of the software that uses the library.

* Yet again, a robust testing strategy can come to the rescue.

#### Replacing a library/technology in a microservice

Changing out the technology used in a microservice should lead to strange side effects.

* Again, vigorous testing is the best strategy to reduce risks.

## Low Risk

Low-risk work will not likely introduce any unpredictability into the development process. Low-risk work:

1. Is easy to undo within a few minutes  
2. Has few unintended side effects and known side effects are well-understood and agreed to by the team  
3. Has little chance to impact someone else on the team in a negative way

### Examples of Low-Risk Work

#### Changing the settings in a configuration file

All settings are externalized into a configuration file if the code is structured well. Changing the settings is easily undone.

#### Adding logging

Adding logging statements to code can enhance our debugging capabilities, is easily undone, and typically has few side effects (other than performance, maybe).

## No Risk

No risk work is guaranteed to introduce no unpredictability into the development process. No risk work:

1. Can be undone instantly or in seconds  
2. Has no side unintended effects  
3. Will not impact someone else on the team in a negative way

### Examples of No Risk Work

#### Adding documentation to existing code

Adding documentation to existing code is a great, low-risk activity that can decrease overall risk.

#### Small Pull Requests

A primary example of no-risk work is small pull requests. Small pull requests (less than 20 lines) typically have no risk and can be accepted and merged quickly.

#### Creating an account or changing permissions

Sometimes, you just need an account for one of our tools or need your permissions changed so that you can complete some task.

# Intensity

Intensity is the amount of work required to complete a task. This is largely dependent on the person doing the work. Consequently, this number should not be assigned until after the team determines who will do the work. Then that person must come up with their estimate. There should always be room to debate who can do the work in less time or how to reduce the time.

We define Intensity as follows:

* High: a week or more of sustained effort  
* Medium: a few days but less than a week  
* Low: a day or less  
* No: a few minutes or seconds

Note that there is a loose correlation between Risk and Intensity. Something that will take more time generally carries with it a more significant risk. The implication is that the longer you have to work on something, the greater the probability that you will introduce a defect or impact someone else, potentially even blocking them. Likewise, something that is high risk will require more time to resolve. Of course, this isn't always the case. You can do a lot of damage in a short amount of time, and it can take forever to complete a piece of low-intensity work. By breaking these two aspects of our estimates apart, we hope to better understand the interplay between them and forecast our performance more accurately to create a more rewarding user experience.

# Ordering

Now that we have a way to determine the weight of an issue, we next need to figure out how to order the work. To do this, we start with a framework to help us think about customer value and then layer in the development velocity for each issue. We can then combine these two dimensions to devise a targeting mechanism for what we work on next.

## Business Value

Business value is defined by perceived client desirability and value. To set this value, the Product Manager is accountable for interpreting client inputs, user research, and market analysis. Business value is defined at a particular point in time and should be reviewed and updated as needed via regular Risk Pool and Backlog grooming sessions. 

Note: Many times in development, there will be technical issues that are not related or are only indirectly related to business value at a given time. In such cases, the issue should be marked as 'No Value', even if the team could conceive of some way it *might* tie to client experience in the future.

|  | Description | Examples |
| :---- | :---- | :---- |
| High Value | 'Must Have' features High-value issues & features must be completed for the product to be considered functional by clients. These tasks have to be done regardless of how they accelerate development velocity.  | Features that define the foundational product, such as the ability to generate Insights Includes must-have features, technical stories that block must-have features, and security issues |
| Medium Value | 'Should Have' features Medium-value tasks will result in features that are important to serve clients and should be delivered, but the product would be functional without them. | Features that are needed to meet customer expectations, such as returning Insights in their preferred file format  |
| Low Value | 'Could Have' features  Low-value tasks are not essential to clients and/or are not time-sensitive but could improve user satisfaction. | Features that might enhance user experience but that aren’t expected, such as updating the UI to return detailed errors about why a batch job failed  |
| No Value | Not related to business value  These tasks may have some value but, at the time of grooming, are not related to any pressing business goal or are entirely technical. | Some 'No Value' tasks might be prioritized if they accelerate development velocity, such as tooling to manage PilotFish configurations in a traceable way via GitHub . |

## Development Velocity Impact

Development Velocity is defined as the number of points (Risk \+ Intensity) burned down over time per team member. Our ideal is roughly 3 story points per team member per day (low risk & low intensity for a given team member). The game, then, is to look for as many ways as possible to reduce risk or intensity. Sometimes, the most significant impact might come from closing another issue\! Velocity impact is measured over three months.

|  | Description  | Examples |
| :---- | :---- | :---- |
| Strong Positive Impact | Increases development velocity such that additional epics can be completed (over a three-month period) | Automating a manual deployment process that takes a few hours every week |
| Weak Positive Impact | Increases development velocity such that additional issues/stories can be completed (over a three-month period) | Refactoring IaC code to correctly tear down infrastructure versus manually destroying it |
| Neutral Impact | No known effect on our velocity | Returning data stored in existing Runtime tables via the user interface based on client requests  |
| Negative Impact | Decreases velocity by a meaningful amount of time, putting issues/stories at risk | Satisfying security requirements can often slow us down, but they are a part of being in the healthcare business |

### 

### 

### Development Priority

Using Business Value and Velocity Impact gives us a path to ordering our work in a way to generates the most client value while balancing dev priorities.

|  | Strong Positive | Weak Positive | Neutral | Negative |
| :---: | :---: | :---: | :---: | :---: |
| High | 21 | 13 | 8 | 5 |
| Medium | 13 | 8 | 5 | 3 |
| Low | 8 | 5 | 3 | 2 |
| None | 5 | 3 | 2 | 1 |

We can now use Risk, Intensity, Value, and Velocity to optimize our way through our work. The team can go after highest priority work first (P-21), then lower priority work next (P-13), etc. Where there are ties amongst the priorities (e.g., several P-5), the team can:

* Use the story points for the issue (calculated with Risk and Intensity)   
* Analyze issue dependencies to sort through the ordering

# Separation of Concerns

Separating concerns is essential in part because it supports our company's value of working as one team by creating a collaborative, inclusive environment to advance our mission.  To this end, Product team members are responsible for determining Business Value and setting it on the issue. *Engineers should not set Business Value*.  Likewise, Engineers are responsible for determining Velocity Impact.  *Product team members should not set Velocity Impact*.


# Grooming 

Regularly grooming the Risk Pool is critical to making this framework operate effectively because all the dimensions used can change over time.

Risk can go down as we learn more. Intensity goes down as we make improvements. Value can change — what was hot yesterday isn’t so important today. Velocity can change — what was less critical yesterday is super essential today and might accelerate us meaningfully. 

Each team should meet once every week, at most every two, to groom their Risk Pools. Grooming the backlog is also critically important, though less pressing than the Risk Pool. Backlog issues tend to age poorly without regular grooming.