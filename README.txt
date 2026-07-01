DECK VISUALIZER — lead-co-sd
============================

WHAT'S IN HERE
  catalog/   the 64-material catalog + 64 swatch images (catalog/swatches/)
  render/    the Gemini render engine + the test command (try_one.py)

ONE-TIME SETUP (do this once)
  1. Open Terminal.
  2. cd into the render folder, e.g.:
         cd ~/Downloads/lead-co-sd/render
  3. Install the two libraries it needs:
         pip3 install requests pillow
  4. Paste in your Gemini key (this terminal window only):
         export GEMINI_API_KEY="AIza...your_key..."
     (To make it stick across new windows, add that line to ~/.zshrc)
  5. Check it's set:
         echo $GEMINI_API_KEY

RUN A TEST RENDER
  You need a deck photo. Use any photo that shows a deck/patio floor —
  one of your own project photos is perfect. Put it in the render folder
  (or use its full path).

      python3 try_one.py my_deck.jpg trex-transcend-lineage-biscayne

  Results land in render/outputs/ :
      <deck>__<material>__after.jpg          the edited image
      <deck>__<material>__before_after.jpg   side-by-side

  See all material ids:
      python3 try_one.py --list

GOOD TO KNOW
  - 7 swatches are REAL Trex photos (the Transcend Lineage colors).
    The other 57 are color-correct stand-ins until real photos are dropped in.
  - Built around RETRY: if a render nudges something it shouldn't, run the
    same command again for a fresh take (~5 sec).
  - numpy is only needed if you REBUILD the swatches (catalog/collect_catalog.py).
    For normal use you don't need it.
