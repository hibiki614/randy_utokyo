## Task 1

### Fundamental technologies of ITS
ITS (Intelligent Transport Systems) is a framework that improves safety, efficiency, environmental performance, and user convenience by enabling a cycle of sensing, integrating/deciding, and informing/controlling in transportation systems.

Fundamental ITS technologies can be broadly grouped into three domains:
- Driver/User support: route guidance, hazard warnings, driving assistance, and human–machine interfaces (HMI)
- Road infrastructure and traffic operations: traffic sensing, signal control, traveler information, and traffic management
- Vehicle-side technologies: onboard sensing, ADAS/automation, and vehicle-to-vehicle/vehicle-to-infrastructure communications

Key enabling technologies include positioning (e.g., GNSS), digital road maps and network databases, traffic sensing (beacons/sensors/cameras/probe data), communications (I2V/V2V/cellular), data platforms (collection, fusion, analytics, distribution), and security/standardization.

### Japan’s nine ITS growth areas (explained one by one)

1) Car navigation systems
- DRM (Digital Road Map) digitalizes road networks as a database and supports route search and travel-time estimation.
- VICS provides real-time information (congestion, regulations, travel times) to support route choice and departure-time adjustments.

2) Electronic Toll Collection (ETC)
- Enables non-stop tolling to mitigate toll-plaza bottlenecks and improve traffic flow and safety.
- ETC2.0 supports large-scale data collection and utilization (e.g., traffic-state monitoring, demand estimation, and road management) through accumulated vehicle travel data.

3) Safety Driving Support
- ACC (Adaptive Cruise Control) enables car-following assistance and may reduce excessive acceleration/deceleration, potentially mitigating the amplification of congestion waves (e.g., at sags).
- AHS-type infrastructure-cooperative support informs drivers in advance about high-risk locations (limited visibility, merges, crash-prone segments), improving hazard awareness.

4) Traffic Control
- Traffic states are measured via beacons/sensors/cameras; then a traffic control center conducts signal operations (offset/split/cycle adjustments) and provides traveler information via VMS and apps.
- Operational measures also include diversion guidance and variable speed management during incidents and road works.

5) Road Maintenance
- Patrol and inspection results can be registered and shared in near real time, improving maintenance decision-making and asset management.
- With advances in image recognition, automated detection of cracks/potholes/sign deterioration and road-surface monitoring (icing/flooding) are increasingly important.

6) Public Transit Operation
- Improves service reliability and convenience through real-time operation management (delay monitoring, dispatch/operations adjustment) and passenger information (arrival prediction, service alerts).
- Integration with roadway operations such as transit signal priority (TSP) can further improve punctuality.

7) Commercial Vehicle Operation
- Supports logistics efficiency (route optimization, ETA management, higher load factors, platooning), addressing congestion, environmental impacts, and labor shortages.
- In dense urban areas, operations should be coordinated with curb/loading management and time-window regulations.

8) Pedestrian Support
- Enhances pedestrian safety (including elderly and persons with disabilities) through crossing assistance, signal information provision, and conflict warnings.
- Benefits are particularly large in pedestrian-concentrated areas such as school zones and station precincts.

9) Emergency Vehicle Operation
- Improves emergency response times through route guidance and signal preemption/priority operations.
- During disasters, rapid integration and sharing of passability and regulation information is essential.

## Task 2
This report selects the United States (USA) as the target country. In the U.S., strong car dependency makes peak-hour congestion a major policy and ITS challenge.

1) Persistent congestion in large metropolitan areas (large time loss)
- A Forbes Japan article (based on INRIX’s congestion ranking) reports that several U.S. cities appear among the world’s most congested and that Los Angeles drivers spend about 104 hours per year in congestion.
- INRIX’s published release on the global congestion ranking also highlights Los Angeles as one of the most congested cities worldwide.
- The Texas A&M Transportation Institute (TTI) reports that U.S. commuters experienced an average of 54 hours of delay in 2022, indicating substantial social and economic losses from congestion.

2) Weak public transit mode share and strong car dependency
- The share of public transit in commuting is small, meaning that congestion cannot be relieved simply by shifting travelers to transit. This strengthens the importance of demand management on roads.

3) High relevance of demand management through pricing
- Given the above conditions, congestion pricing and dynamically priced managed lanes become realistic and scalable tools to reduce peak demand, stabilize traffic flow, and provide funding for operations and alternatives.


## Task 3
### Proposed solution package for the U.S.: Pricing as the core policy, supported by ITS

A) CBD/Cordon Congestion Pricing (downtown pricing)
- Policy concept: charge vehicles entering a defined central area to reduce peak demand and improve reliability.
- ITS requirements: free-flow tolling using ANPR (automatic number plate recognition), electronic payment, account management, and enforcement systems.
- Practical reference: London’s congestion charge provides a clear example of camera-based plate recognition and area-based charging. Stockholm’s cordon pricing is also widely discussed as a reference case with explicit operational and governance considerations.

B) Dynamically priced managed lanes (HOT/Express lanes)
- Policy concept: adjust tolls in real time to maintain reliable speeds in priced lanes, while keeping general-purpose lanes available.
- ITS requirements: real-time traffic detection, pricing algorithms, dissemination via variable message signs and apps, and electronic toll collection.

C) Implementation conditions (acceptability and governance)
- Revenue use: clarify how revenue is used (e.g., operations, maintenance, safety, transit/DRT support) to improve legitimacy.
- Fairness: consider discounts, caps, and complementary services for low-income users and essential trips.
- Privacy and data governance: establish clear rules on data use, retention, and third-party sharing.

### Key difference from Japan: technology readiness vs. pricing acceptance and behavior change

Japan has strong technical infrastructure for toll collection (high ETC penetration), but widespread acceptance of pricing as a primary congestion-management tool is still developing. This issue is less about hardware feasibility and more about awareness, willingness to change behavior, and perceived fairness.

Evidence from a Japanese time-variable pricing experiment (Tokyo Bay Aqua-Line) suggests that:
- only 35% knew the detailed content of the experiment, and
- even among those who knew the details, 42% changed their behavior.
This indicates that policy design must be combined with communication, user-friendly information, and perceived fairness to induce behavior change.

Therefore, compared to the U.S. where pricing can be positioned as a central demand-management policy under strong car dependency, Japan may require more emphasis on social acceptance measures such as outreach, transparency, and fairness design in addition to ITS implementation.


## 参考文献 / References

日本語文献
- Forbes JAPAN (2017) 「交通渋滞が最もひどい都市　米国5都市がトップ10にランクイン」 https://forbesjapan.com/articles/detail/15429
- 欧州における道路課金の最新の動向（道路新産業開発機構）
	- https://www.hido.or.jp/itsapq/jsp/auth/trab/no93/tokusyu13-20.pdf
- 混雑等に応じた柔軟な料金について（国土交通省）
	- https://www.mlit.go.jp/policy/shingikai/content/001856687.pdf

English references
- INRIX (2017) Los Angeles tops INRIX Global Congestion Ranking 2016.
	- https://inrix.com/press-releases/los-angeles-tops-inrix-global-congestion-ranking/?utm_source=chatgpt.com
- Texas A&M Transportation Institute (TTI) (2023/2024) Urban Mobility Report (delay hours and related indicators).
	- https://tti.tamu.edu/2024/06/tti-publishes-2023-urban-mobility-report/?utm_source=chatgpt.com

