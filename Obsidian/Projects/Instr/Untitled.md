1. Research Background and Problem Awareness
    Clarify the starting point of this study and the necessity of focusing on travel speed.
        Identify the gap between the assumptions underlying conventional signal coordination theory and the realities of urban traffic and emerging autonomous driving societies.
    Figure:
    Not required (chapter title)

1.1 Conventional Assumptions in Signal Coordination Theory
    In conventional signal coordination theory, travel speed V has been treated as a fixed value.
        In previous studies, the main design variables in signal coordination have been link length L,
        cycle length C, and offset x,
        while travel speed V has often been implicitly treated as a given constant.
        Speed has been positioned as an assumption outside the scope of the theory.
    Figure:
    Schematic diagram showing design variables (L, C, x) and fixed condition (V)

1.2 Actual Operating Speeds in Urban Traffic
    In urban areas, there is a large discrepancy between speed limits and actual operating speeds.
        Even on roads with speed limits of 50–60 km/h in urban areas,
        actual average travel speeds are often below 20 km/h.
        Signal stops and congestion govern the average speed,
        indicating that speed is not an exogenous condition
        but rather an outcome of the traffic system.
    Figure:
    Schematic diagram comparing speed limits and actual operating speeds

1.3 Traffic Simulation Case Study in the Kashiwa-no-ha Area
    Traffic simulations were conducted assuming low-speed automated buses.
        In the Kashiwa-no-ha area, considering the maturity of automated driving technology,
        safety requirements, and the characteristics of shared mobility (bus services),
        a low-speed operation scenario without assuming high-speed travel was adopted.
    Figure:
    Simplified network diagram of the Kashiwa-no-ha area

1.4 Automated Vehicles as Pace Makers
    Automated buses acted as pace makers and determined corridor-wide speeds.
        Simulation results showed that,
        in mixed traffic conditions, low-speed automated buses functioned as pace makers,
        determining the actual operating speed of the entire corridor.
        This suggests that speed is not merely an outcome,
        but an important operational variable.
    Figure:
    Schematic diagram of a leading automated vehicle and following vehicles

1.5 Problem Statement of This Study
    Do not exclude low-speed options and question the meaning of varying speed.
        This study does not claim that low speed is always desirable.
        Rather, it raises the question of whether we should theoretically understand
        how signal coordination effects behave
        when speed is varied.
    Figure:
    Not required

2. Theoretical Organization of Signal Coordination Effects
    Define and organize signal coordination effects using a one-link, two-intersection model.
        This chapter organizes the essence of signal coordination effects
        using the minimum unit model of one link and two intersections.
    Figure:
    Not required (chapter title)

2.1 What Is a Signal Coordination Effect?
    Signal coordination effects represent the sensitivity of delay to offset.
        A situation in which a slight change in offset x
        causes a large change in average delay.
        Rather than focusing on the presence or absence of green waves,
        attention is paid to the delay structure itself.
    Figure:
    Comparison diagram of high and low coordination effects (green wave)

2.2 One-Link, Two-Intersection Model
    Multi-intersection problems can be understood as combinations of one-link, two-intersection models.
        A model is considered in which an upstream and a downstream intersection
        are connected by a single link.
        A constant speed V is assumed within the link,
        and both intersections share a common cycle length C.
    Figure:
    Basic schematic diagram of the one-link, two-intersection model

2.3 Definition of Delay
    Average delay is defined as the mean of delays in both directions.
        Let d12 be the delay in the upstream-to-downstream direction,
        and d21 be the delay in the downstream-to-upstream direction.
        The bidirectional average delay is defined as
        d = (d12 + d21) / 2.
    Figure:
    Not required (equation-centered)

2.4 Mathematical Representation of Delay
    Delay is a function of offset x and normalized link length Λ.
        The average delay is expressed as
        d = d(x, Λ).
        The equation represents arrival phases and red-signal waiting times,
        and this study focuses on analyzing the structure of this function itself.
    Figure:
    Delay–offset curve (d–x) published in IATSS Research

2.5 Definition of Normalized Link Length Λ
    Λ is a dimensionless quantity integrating link length, cycle length, and speed.
        The normalized link length Λ is defined as
        Λ = L / (C V).
        The delay structure can be systematically organized using Λ.
    Figure:
    Schematic diagram illustrating the physical meaning of Λ

2.6 Fundamental Results by Newell and Koshi
    Periodic structures of coordination effects were shown under saturated and symmetric conditions.
        The conditions are saturated traffic and green ratios g1 = g2 = 0.5.
        Under these conditions,
        coordination effects are high when Λ = n / 2,
        and low when Λ = n / 4.
    Figure:
    Representative figure by Newell and Koshi

2.7 Generalization by Sakakibara and Oguchi
    Similar structures were confirmed under undersaturated and asymmetric conditions.
        Analyses considering undersaturated conditions, green ratios g1 ≤ g2,
        and demand ratio P were conducted.
        As shown in Fig. 12,
        periodic coordination effect structures with respect to Λ were confirmed.
    Figure:
    Fig. 12 (from the paper)

3. Focus and Methodology of This Study
    This study varies speed and cycle length rather than link length.
        Focusing on Λ = L / (C V),
        the study examines how the corresponding link length L changes
        when C and V are varied
        within the range Λ = 0–1.
    Figure:
    Not required (chapter title)

3.1 Limitations of Previous Studies
    Λ has been discussed, but C and V have been fixed.
        Discussions have effectively been limited to varying link length L,
        and the effects of speed and cycle length have not been sufficiently organized.
    Figure:
    Not required

3.2 Basic Stance of This Study
    Coordination effects can change even for the same physical link length.
        Even when the physical link length L is the same,
        changing C or V alters Λ,
        which in turn changes the strength of coordination effects.
    Figure:
    Not required

3.3 Structure of the Visualization Tool
    Visualize delay structures in three dimensions.
        x-axis: offset x
        y-axis: link length L
        z-axis: average delay d
        Only the range Λ = 0–1 is displayed,
        and V and C can be freely manipulated.
    Figure:
    Visualization tool interface (3D surface)

3.4 Fundamental Relationships Derived from Visualization
    Increasing C or V increases the corresponding L for the same Λ.
        This is intuitively understood from the form of Λ = L / (C V),
        and is also confirmed by the visualization results.
    Figure:
    Comparison of cross sections at identical Λ

3.5 Key Implications of This Study
    Speed and cycle length are operational variables that influence coordination effects.
        By adjusting speed and cycle length,
        coordination effects can either be strengthened or weakened,
        depending on the conditions.
    Figure:
    Comparison of delay curves under the same link length

4. Numerical Examples and Implications for Multi-Intersection Corridors
    Connect theoretical results to numerical examples and multi-intersection problems.
        Numerical examples are used to examine
        how speed conditions affect multi-intersection structures.
    Figure:
    Not required (chapter title)

4.1 Numerical Conditions
    A corridor with multiple intersections having identical link lengths is assumed.
        Calculations are conducted by changing only speed conditions,
        while keeping all other conditions fixed.
    Figure:
    Schematic diagram of calculation settings

4.2 Results for a Three-Intersection Model
    Dominant intersection pairs change depending on speed conditions.
        Differences in speed conditions alter
        which intersection pairs exhibit prominent coordination effects,
        resulting in changes in the dominant structure.
    Figure:
    Results for the three-intersection model

5. Connection to Previous Studies: The Concept of Critical Intersections
    Critical intersections are a theoretical concept for evaluation.
        The concept of critical intersections in multi-intersection corridors
        and the division of roles between theory and design are organized.
    Figure:
    Not required (chapter title)

5.1 Definition of Critical Intersections
    Critical intersections are intersections or intersection pairs that dominate the corridor.
        Critical intersections are defined as combinations
        that minimize delay in the two-intersection theory.
    Figure:
    Schematic diagram of the critical intersection concept

5.2 Role in Previous Studies
    Critical intersections and theoretical lower bounds are tools for evaluation and assurance.
        Actual offset design is conducted through PI-minimization searches,
        while theory is used to evaluate the validity of the design results.
    Figure:
    Relationship diagram between theory (evaluation) and search (design)

5.3 Changes Induced by Variable Speed
    Changing speed can also alter critical intersections and theoretical lower bounds.
        Changing V alters Λ,
        which changes the structure of d(x, Λ),
        and thus may change critical intersections and theoretical lower bounds.
    Figure:
    Schematic diagram of structural changes due to speed conditions

6. Summary and Future Perspectives
    Summarize the results of this study and future challenges.
        Clarify the positioning of this study
        and indicate future directions.
    Figure:
    Not required (chapter title)

6.1 Summary of This Study
    Signal coordination effects without fixed-speed assumptions were organized.
        The relationships among C, V, and L were organized using Λ as a key axis,
        providing a new understanding of coordination effects.
    Figure:
    Not required

6.2 Future Perspectives
    Extend toward coordinated design of signals and speed.
        Future challenges include
        segment-wise speed settings
        and simultaneous optimization of offsets and speed.
    Figure:
    Conceptual schematic of signal–speed coordination
