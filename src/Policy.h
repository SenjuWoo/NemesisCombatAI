// Pure combat-mind policy: who an NPC is and what is happening around it decide how much nerve it has.
// Movesets, attacks and animation graphs belong to For Honor / BFCO and are never touched here.
#pragma once

#include <algorithm>
#include <array>
#include <atomic>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <optional>
#include <string_view>
#include <unordered_set>
#include <vector>

namespace NCAI
{
    enum class Doctrine { Neutral, Military, Bandit, Forsworn, Thalmor, Vampire, Daedra, Undead, Caster, Construct };
    enum class Tier { Rabble, Trained, Veteran, Elite };

    struct Profile
    {
        Doctrine doctrine = Doctrine::Neutral;
        float level = 1.0F;
        float skill = 0.0F;  // best combat skill, 0..100
        float rank = 0.0F;   // rank in the doctrine faction, 0 when unranked
        float gear = 0.0F;   // 0..1 equipment quality; 0 when the gear option is off
        bool unique = false;
        bool titled = false; // name carries a leader title (Captain, Chief, Jarl ...)
        bool boss = false;   // uses a vanilla boss combat style
        bool master = false; // For Honor picked this fighter as a weapon master (it carries FH's perk)
        bool person = true;  // race carries ActorTypeNPC; creatures (Falmer, giants, spriggans ...) never rout
    };

    // What the race says about a fighter. Draugr, skeletons, Falmer, giants, atronachs and Dwarven constructs are
    // creatures in the race data (no ActorTypeNPC), and most of them belong to no faction the doctrine table knows.
    struct RaceTraits
    {
        bool person = true;     // ActorTypeNPC
        bool undead = false;    // ActorTypeUndead
        bool daedra = false;    // ActorTypeDaedra
        bool construct = false; // ActorTypeDwarven
        bool vampire = false;   // Vampire
    };

    // The dead, the daedric and the mechanical do not know fear, whatever faction they are in; a vampire or a dremora
    // without a known faction still fights like one. Otherwise the faction decides.
    [[nodiscard]] constexpr Doctrine RaceDoctrine(Doctrine a_fromFactions, const RaceTraits& a_race) noexcept
    {
        if (a_race.construct) return Doctrine::Construct;
        if (a_race.undead && !a_race.vampire) return Doctrine::Undead;   // skeletons, ghosts, Draugr, ash spawn
        if (a_race.daedra && !a_race.person) return Doctrine::Daedra;    // atronachs and other daedric creatures
        if (a_fromFactions == Doctrine::Neutral) {
            if (a_race.vampire) return Doctrine::Vampire;
            if (a_race.daedra) return Doctrine::Daedra;
        }
        return a_fromFactions;
    }

    // Leader titles, matched as whole words so "King" never matches inside another name.
    inline constexpr std::string_view kTitles[] = { "Boss", "Chief", "Chieftain", "Champion", "Warlord", "Commander",
        "General", "Jarl", "Captain", "Master", "Veteran", "Thane", "Lord", "King", "Queen", "Leader" };

    [[nodiscard]] inline bool HasTitle(std::string_view a_name) noexcept
    {
        const auto letter = [](char c) { return std::isalpha(static_cast<unsigned char>(c)) != 0; };
        for (const auto title : kTitles) {
            for (auto at = a_name.find(title); at != std::string_view::npos; at = a_name.find(title, at + 1)) {
                const auto end = at + title.size();
                if ((at == 0 || !letter(a_name[at - 1])) && (end == a_name.size() || !letter(a_name[end]))) return true;
            }
        }
        return false;
    }

    // A fixed set of form IDs that the game thread writes and any thread may read without a lock. Event callbacks
    // use it to drop events about actors nobody tracks before they cost a queued task.
    template <std::size_t N>
    class IdMirror
    {
    public:
        bool Add(std::uint32_t a_id) noexcept
        {
            if (a_id == 0) return false;
            if (Contains(a_id)) return true;
            for (auto& slot : slots_) {
                if (slot.load(std::memory_order_relaxed) == 0) {
                    slot.store(a_id, std::memory_order_release);
                    return true;
                }
            }
            return false;
        }
        void Remove(std::uint32_t a_id) noexcept
        {
            if (a_id == 0) return;
            for (auto& slot : slots_) {
                if (slot.load(std::memory_order_relaxed) == a_id) slot.store(0, std::memory_order_release);
            }
        }
        [[nodiscard]] bool Contains(std::uint32_t a_id) const noexcept
        {
            if (a_id == 0) return false;
            for (const auto& slot : slots_) {
                if (slot.load(std::memory_order_acquire) == a_id) return true;
            }
            return false;
        }
        void Clear() noexcept
        {
            for (auto& slot : slots_) slot.store(0, std::memory_order_release);
        }

    private:
        std::array<std::atomic<std::uint32_t>, N> slots_{};
    };

    struct Situation
    {
        float health = 1.0F;       // current / maximum health
        unsigned allies = 0;       // living friends fighting within range
        unsigned foes = 1;         // living enemies fighting within range
        unsigned casualties = 0;   // friends that died nearby recently
        bool leaderNear = false;   // a clearly more capable friend is alive nearby
        bool leaderDown = false;   // such a friend died nearby recently
        float foeLevel = 1.0F;     // level of the current target
        bool foeRanged = false;
        bool lastStandActive = false; // previous verdict, gives the rage an exit threshold
        bool groupAware = true;
        bool situational = true;
        bool lastStand = true;
    };

    struct Mind
    {
        float intellect = 0.0F;      // 0..1
        Tier tier = Tier::Rabble;
        float confidenceShift = 0.0F; // added to the actor's authored Confidence
        bool lastStand = false;
        bool routed = false;         // the pack is breaking: the only case that may push an enemy into running
    };

    inline float Bounded(float value, float low, float high, float fallback)
    {
        return std::isfinite(value) ? std::clamp(value, low, high) : fallback;
    }

    constexpr float kEliteFloor = 0.60F;  // lowest Intellect that TierOf() calls Elite

    // Level and trained skill dominate; rank and rare titles lift individual leaders above their peers.
    inline float Intellect(const Profile& p)
    {
        const float level = (Bounded(p.level, 1.0F, 40.0F, 1.0F) - 1.0F) / 39.0F;
        const float skill = Bounded(p.skill, 0.0F, 100.0F, 0.0F) / 100.0F;
        const float rank = Bounded(p.rank, 0.0F, 6.0F, 0.0F) / 6.0F;
        const float gear = Bounded(p.gear, 0.0F, 1.0F, 0.0F);
        const float value = 0.35F * level + 0.30F * skill + 0.10F * rank + 0.05F * gear
            + (p.unique ? 0.10F : 0.0F) + (p.titled ? 0.15F : 0.0F) + (p.boss ? 0.15F : 0.0F);
        // For Honor only picks masters of steel, so the brain treats them as Elite whatever their level says.
        return std::clamp(p.master ? std::max(value, kEliteFloor) : value, 0.0F, 1.0F);
    }

    inline Tier TierOf(float intellect)
    {
        if (intellect < 0.20F) return Tier::Rabble;
        if (intellect < 0.40F) return Tier::Trained;
        if (intellect < 0.60F) return Tier::Veteran;
        return Tier::Elite;
    }

    // Dynamic Grip lets an NPC swap between one- and two-handed grips mid-fight. Only schooled fighters get that,
    // and never a For Honor master: DG's OAR replacers outrank most For Honor ones, so a swap would replace its moveset.
    inline bool GripSchooled(Tier tier, Doctrine doctrine, bool master)
    {
        return !master && tier >= Tier::Trained && doctrine != Doctrine::Caster;
    }

    // Whether an NPC's base should carry Dynamic Grip's blacklist keyword. A For Honor master always does, whatever
    // the grip option says; everyone else only while the option is on and they are not schooled.
    inline bool GripBlockWanted(bool tiersOn, Tier tier, Doctrine doctrine, bool master)
    {
        return master || (tiersOn && !GripSchooled(tier, doctrine, master));
    }

    // Which of a pool's two styles an NPC gets: stable per NPC so a save always sees the same fighter.
    inline unsigned PoolSlot(unsigned formId)
    {
        return (formId >> 4) & 1U;
    }

    inline bool Fearless(Doctrine d)
    {
        return d == Doctrine::Undead || d == Doctrine::Daedra || d == Doctrine::Construct;
    }

    inline Mind Think(const Profile& p, const Situation& s)
    {
        // Per tier: resting nerve, how strongly morale swings move it, and how health loss erodes it.
        static constexpr float kNerve[] = { -0.75F, 0.0F, 0.25F, 0.5F };
        static constexpr float kSway[] = { 1.5F, 1.0F, 0.7F, 0.4F };
        static constexpr float kPain[] = { 1.0F, 0.75F, 0.5F, 0.25F };

        Mind mind;
        mind.intellect = Intellect(p);
        mind.tier = TierOf(mind.intellect);
        const auto t = static_cast<std::size_t>(mind.tier);
        const float health = Bounded(s.health, 0.0F, 1.0F, 1.0F);

        float morale = 0.0F;
        if (s.groupAware) {
            morale += 0.25F * static_cast<float>(std::min(s.allies, 4U));   // safety in numbers
            morale -= 0.5F * static_cast<float>(std::min(s.casualties, 4U)); // friends dropping around you
            if (s.leaderNear) morale += 0.75F;
            if (s.leaderDown) morale -= 1.0F;
            if (s.foes > s.allies + 1) {
                morale -= 0.5F * static_cast<float>(std::min(s.foes - s.allies - 1, 2U)); // outnumbered
            }
        }
        if (s.situational) {
            const float gap = (Bounded(s.foeLevel, 1.0F, 100.0F, 1.0F) - Bounded(p.level, 1.0F, 100.0F, 1.0F)) / 10.0F;
            if (gap > 0.0F) morale -= 0.5F * std::min(gap, 2.0F); // facing something far stronger
            if (s.foeRanged && mind.tier >= Tier::Trained) morale += 0.5F; // trained fighters rush archers
        }

        float shift = kNerve[t] + morale * kSway[t];
        shift -= std::clamp((0.5F - health) / 0.5F, 0.0F, 1.0F) * kPain[t];

        switch (p.doctrine) {
        case Doctrine::Military:
            if (s.groupAware && s.allies > 0 && !s.leaderDown) shift += 0.25F; // discipline holds the line
            break;
        case Doctrine::Bandit:
            if (s.groupAware && s.casualties > 0) shift -= 0.25F; // mercenary nerve
            break;
        case Doctrine::Forsworn:
        case Doctrine::Thalmor:
            shift += 0.25F;
            break;
        case Doctrine::Vampire:
            if (health > 0.5F) shift += 0.25F;
            break;
        default:
            break;
        }

        if (Fearless(p.doctrine)) {
            shift = std::max(shift, 1.0F);
        }

        // A pack breaks; a lone survivor does not (nobody to run with, and a chase is no fun for the player). Only
        // untrained people rout, and only when their leader fell or they are visibly losing the crowd - and a leader
        // still standing beside them holds the line: kill the chief to break the band.
        mind.routed = s.groupAware && p.person && mind.tier == Tier::Rabble && !Fearless(p.doctrine) && s.allies > 0
            && (s.leaderDown || (!s.leaderNear && s.casualties >= 2 && s.allies < s.casualties));
        if (mind.routed) shift = std::min(shift, -2.5F);

        // Experienced fighters turn desperate instead of breaking; the rage ends once they recover.
        const float exitHealth = s.lastStandActive ? 0.5F : 0.25F;
        mind.lastStand = s.lastStand && mind.tier >= Tier::Veteran && health < exitHealth
            && p.doctrine != Doctrine::Thalmor && p.doctrine != Doctrine::Caster;
        if (mind.lastStand) shift = std::max(shift, 2.0F);

        // Quantized so tiny fluctuations never cause repeated writes.
        mind.confidenceShift = std::round(std::clamp(shift, -2.5F, 2.5F) * 4.0F) / 4.0F;
        return mind;
    }

    // ---- modifier contract, shared by the runtime and its host tests ----
    // Co-save v1 (3.0.0-3.0.2) stored a delta that those builds applied as |delta| on the damage channel, so the
    // record no longer describes what the engine actually holds. v2 stores the signed permanent delta this build owns.
    inline constexpr std::uint32_t kLegacyCoSaveVersion = 1;
    inline constexpr std::uint32_t kCoSaveVersion = 2;

    [[nodiscard]] constexpr bool RestorableCoSave(std::uint32_t a_version) noexcept { return a_version >= kCoSaveVersion; }

    // The delta a release applies to take our permanent change back off again.
    [[nodiscard]] constexpr float RevertDelta(float a_applied) noexcept { return -a_applied; }

    // Authored confidence as seen through our own applied delta. Feed it the PERMANENT value (base + permanent
    // modifiers): temporary effects such as fear or rally sit on top and must neither be mistaken for the authored
    // value nor be cancelled by our shift.
    [[nodiscard]] constexpr float AuthoredBase(float a_current, float a_applied) noexcept { return a_current - a_applied; }

    // Confidence stays on the engine's authored scale.
    [[nodiscard]] inline float ClampConfidence(float a_value) noexcept { return std::clamp(a_value, 0.0F, 4.0F); }

    // How readily this plugin may make an enemy run. The engine reads Confidence as willingness to fight a stronger
    // foe (UESP, Skyrim:NPCs): 4 Foolhardy fights to the death, 3 Brave attacks unless outmatched, 2 Average avoids
    // higher-level opponents, 1 Cautious attacks only lower-level ones, 0 Cowardly flees at low health. Vanilla
    // bandits, Draugr and most soldiers are Foolhardy, so any flight a lowered value causes is this plugin's doing.
    //   Never: Confidence is never lowered.
    //   Rare (default): ordinary pressure never lowers it; only a routing pack may, down to Average.
    //   Often: ordinary pressure may lower it to Brave, a routing pack down to Cautious.
    enum class Fleeing { Never, Rare, Often };

    struct Floors { float calm; float rout; };

    [[nodiscard]] constexpr Floors FloorsFor(Fleeing a_mode) noexcept
    {
        switch (a_mode) {
        case Fleeing::Never: return { 4.0F, 4.0F };
        case Fleeing::Often: return { 3.0F, 1.0F };
        default: return { 4.0F, 2.0F };
        }
    }

    [[nodiscard]] inline std::optional<Fleeing> ParseFleeing(std::string_view a_text) noexcept
    {
        if (a_text == "never" || a_text == "0") return Fleeing::Never;
        if (a_text == "rare" || a_text == "1") return Fleeing::Rare;
        if (a_text == "often" || a_text == "2") return Fleeing::Often;
        return std::nullopt;
    }

    [[nodiscard]] constexpr const char* FleeingName(Fleeing a_mode) noexcept
    {
        return a_mode == Fleeing::Never ? "never" : a_mode == Fleeing::Often ? "often" : "rare";
    }

    // The Confidence an enemy should have: the authored value moved by the shift, but never below the floor for the
    // situation. A floor above the authored value means "leave it alone", so a base that is already low stays put.
    [[nodiscard]] inline float WantedConfidence(float a_base, float a_shift, bool a_routed, Fleeing a_mode) noexcept
    {
        const Floors floors = FloorsFor(a_mode);
        const float floor = std::min({ a_base, a_routed ? floors.rout : floors.calm, 4.0F });
        return std::clamp(ClampConfidence(a_base + a_shift), floor, 4.0F);
    }

    // One grading pass per world. The graded flag is separate from the generation on purpose: a world generation of
    // 0 is a real world, and a pass that failed or was skipped must not look like one that succeeded.
    struct GradeState
    {
        bool graded = false;
        std::uint32_t generation = 0;

        [[nodiscard]] bool NeedsPass(std::uint32_t a_world) const { return !graded || generation != a_world; }
        void Recorded(std::uint32_t a_world) { graded = true; generation = a_world; }
        void Reset() { graded = false; generation = 0; }
    };

    // Ownership bookkeeping for Dynamic Grip, held in one place so a release cannot forget half of it.
    struct GripLedger
    {
        std::unordered_set<std::uint32_t> blocked;  // bases where this plugin added the blacklist keyword

        [[nodiscard]] bool OwnedByUs(std::uint32_t a_base) const { return blocked.contains(a_base); }
        void Block(std::uint32_t a_base) { blocked.insert(a_base); }
        // Take one base back off the ledger; true when it was ours.
        bool TakeBack(std::uint32_t a_base) { return blocked.erase(a_base) > 0; }

        // Every base whose keyword must be removed. The ledger is empty afterwards even when nothing was owned.
        [[nodiscard]] std::vector<std::uint32_t> ReleaseAll()
        {
            std::vector<std::uint32_t> out(blocked.begin(), blocked.end());
            blocked.clear();
            return out;
        }
    };

    // A keyword may be removed by us only if we added it and it is still on the base.
    [[nodiscard]] constexpr bool OwnsKeyword(bool a_addedByUs, bool a_present) noexcept { return a_addedByUs && a_present; }
}
