# Interface Plan

## Architecture
We will use FastAPI to connect our frontend and backend. We will also use Streamlit to create our frontend since it is user-friendly, Python-native and time efficient given our deadlines.

## Search Functionality
The goal is to allow users to interactively learn about our corpus and annotations. The example text fields will be searchable for every example in entire corpus. In terms of metadata, the misinformation label (0 for factual, 1 for misinformation) will also be searchable. Users will be able to scroll through the examples that are returned by the keyword search. Given that our search functionality is fairly simple, we will use Whoosh to implement it, as it is lightweight and suited to smaller applications.

## Annotation Display
Annotations will be displayed via an "Annotated examples only" checkbox, which restricts search results to examples that have been annotated. Each matching example is displayed with its ID, text, and annotation tags.

After searching, the user can also filter search results by annotation tag. Each annotation tag will have a button that the user can click to filter by that tag. We think buttons are preferable to a drop-down menu as each of the five options are immediately visible to the user. 

Annotation tags are colour coded throughout the interface. The annotated text within each example will be highlighted in the colour corresponding to the relevant tag. 

We will also include a tag distribution bar chart that shows the frequency of each annotation tag within the matching search results. This will update with every search and the bar chart colours will match the annotation tag colours. This gives the user an overall picture of the tag distribution at a glance, without needing to read through each example individually, and offers high-level understanding of the corpus.

An overall Fleiss' κ score for the entire 1000 annotated examples will be recorded in the top right corner, for interest.

Lastly, a static tag legend will appear below the chart, with a brief description of each annotation tag. A link to the lexicon used to match hedging words will also be provided in the description for the hedging tag.

## User Experience
Further to features detailed above, we will include visual feedback throughout, including the following on mouse-hover:

- lift of the boxes containing each example returned by search;
- buttons become highlighted; and
- the Fleiss' κ badge glows.

## Stretch Goal
If feasible given our timeframe, we will also include a second corpus on the backend that contains AI annotations. On the frontend, we will add an additional checkbox allowing the user to select to show AI annotations. This offers the user insight in to how AI's annotations compare to those of our main corpus. The main corpus annotations were deemed best based on human judgment, through Inter-annotator agreement.
