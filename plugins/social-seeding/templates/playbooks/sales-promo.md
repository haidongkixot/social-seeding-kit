# Playbook: sales and promotion

**Status:** DRAFT. Replace the examples with your own, then record the language review in `config/caps.toml` `[languages]`. Every message also follows `playbooks/<language>-style.md` if it exists.

The examples are **patterns, not templates.** The writer always rewrites them for the actual thread, and never posts the same sentence twice within `duplicate_window_days`. Placeholders: `{brand}`, `{rep}`, `{category}`, `{destination}`.

## Where this playbook applies
- **Boards (`kind = "board"`):**
  - buyer posts that mention a product from the catalog;
  - our own offer posts (only where `promo_posts = "yes"`, at most 1 per group per day).
- **Discussion groups and pages:** questions about suppliers or products we carry.

## Stage moves
| Stage | Goal | Signals to watch | Move | Don't |
|---|---|---|---|---|
| 0 SEED (a buyer post) | Be the useful reply | a buyer phrase + a product we carry | Answer what they asked: what we have, by quantity. Ask one question (city or volume). No link. | Paste an ad; mention price; post a link |
| 0 SEED (our offer post) | Get people to comment | none | A short teaser: categories, "by quantity", flexible terms, "comment your city". No link in the post. | List prices; emoji walls; repeat yesterday's text |
| 1 ENGAGED | Learn the need | They replied to us | Answer their point, then ask 1 question: city, volume or which product. | Ask several questions at once |
| 2 QUALIFIED | Offer the next step | Asks price, payment, delivery or contact; says they are interested | Say price and terms depend on volume and city, and that the funnel destination has the details and direct contact. Ask: "Shall I send you the link?" | Send the link before they say yes |
| 3 INVITED | Send the link | They say yes | The link for the conversation's category from `funnel.toml`, in the thread only if `links = "yes"`, otherwise by DM (they asked, and the DM is approved). | Send both links when only one fits |
| 4 JOINED | Close the loop | The owner sees them join | Optional welcome by the owner at the destination. Close the conversation file. | none |
| X CLOSED | Stop | `max_unanswered_turns` unanswered turns, negative words, admin note | Nothing. | Argue; reply to trolls |

## Example patterns (replace with your language and products)

**Buyer post** ("Looking for detergent in bulk"):
> Hi, I am {rep}, from {brand}. We have detergent by the pallet. Roughly what quantity do you need?

**Offer post** (board):
> Greetings to small businesses. At {brand} we have {category} by quantity, with flexible terms. We are looking for customers and distributors in new cities. Comment your city and we will tell you more.

**ENGAGED to QUALIFIED:**
> Perfect. Price depends on volume and city, and terms are flexible. We give all the details in our group for bulk customers. Shall I send you the link?

### Group replies with tags
When several people commented on the same post and need the **same answer**, answer once and tag the others instead of writing near-identical replies.
- Reply under one person's comment (the main recipient) and tag **0 to `max_extra_tags` other people** in the text. The number is random each time, and the main recipient doesn't count.
- Tag only people who **commented on that same post** and are **waiting for that same answer**. Never tag anyone else.
- Don't tag someone whose last message we already answered and who hasn't replied since. A tag is one of our turns for each tagged person, so it adds to their `unanswered_turns`.
- Write to the group, not to one person, and use the plural form of the language.
- One tagged reply counts as one item for the caps.

### Inbound Messenger (`dm_inbound`)
A person who commented on our posts writes to the owner in Messenger. They contacted us, so this isn't a cold DM. Every reply still needs the owner's approval. Ask for their contact and the product they want, so an advisor can follow up, and send only the matching funnel link when the category is known.

## Objections
Add one block per recurring objection: the objection, the calm answer, and the question that moves the person to QUALIFIED. Never name payment methods, banks or currencies in public unless a knowledge file allows it.
