// Host checks for the combat-mind policy. The release mode defines NDEBUG, which would compile every assert below
// out and leave a test that always passes, so it is undefined here, in the file, where no build flag can undo it.
#undef NDEBUG
#include "Policy.h"

#include <cassert>
#include <cmath>
#include <cstdio>

using namespace NCAI;

static Profile Grunt() { return { Doctrine::Bandit, 5.0F, 20.0F, 0.0F, 0.0F, false, false, false }; }
static Profile Chief() { return { Doctrine::Bandit, 25.0F, 70.0F, 3.0F, 0.0F, true, true, true }; }
static Profile Legend() { return { Doctrine::Military, 45.0F, 95.0F, 6.0F, 1.0F, true, true, true }; }

int main()
{
    // Tiering follows level, skill, rank and titles.
    assert(Think(Grunt(), {}).tier == Tier::Rabble);
    assert(Think(Chief(), {}).tier >= Tier::Veteran);
    assert(Think(Legend(), {}).tier == Tier::Elite);
    assert(Intellect(Chief()) > Intellect(Grunt()));

    // Rabble start shaky; elites keep composure.
    assert(Think(Grunt(), {}).confidenceShift < 0.0F);
    assert(Think(Legend(), {}).confidenceShift > 0.0F);

    // Rabble routs when friends fall and the leader dies; elites barely notice.
    Situation rout;
    rout.allies = 1;
    rout.foes = 4;
    rout.casualties = 3;
    rout.leaderDown = true;
    const float rabbleRout = Think(Grunt(), rout).confidenceShift;
    const float eliteRout = Think(Legend(), rout).confidenceShift;
    assert(rabbleRout <= -2.0F);
    assert(eliteRout > rabbleRout + 1.5F && eliteRout >= -1.0F);

    // A pack with a leader emboldens low tiers more than lone fighters.
    Situation pack;
    pack.allies = 4;
    pack.leaderNear = true;
    assert(Think(Grunt(), pack).confidenceShift > Think(Grunt(), {}).confidenceShift + 1.0F);

    // Group and situational switches really disable their inputs.
    Situation off = rout;
    off.groupAware = false;
    off.situational = false;
    assert(Think(Grunt(), off).confidenceShift == Think(Grunt(), {}).confidenceShift);

    // Fearless doctrines never drop below a bold floor, whatever the morale.
    Profile zombie = Grunt();
    zombie.doctrine = Doctrine::Undead;
    assert(Think(zombie, rout).confidenceShift >= 1.0F);

    // Last stand: veterans turn desperate below 25% and calm down above 50%; casters and rabble never rage.
    Situation hurt;
    hurt.health = 0.2F;
    assert(Think(Chief(), hurt).lastStand && Think(Chief(), hurt).confidenceShift >= 2.0F);
    Situation calming = hurt;
    calming.health = 0.4F;
    calming.lastStandActive = true;
    assert(Think(Chief(), calming).lastStand);
    calming.health = 0.55F;
    assert(!Think(Chief(), calming).lastStand);
    Profile mage = Chief();
    mage.doctrine = Doctrine::Caster;
    assert(!Think(mage, hurt).lastStand);
    assert(!Think(Grunt(), hurt).lastStand);

    // Low health erodes nerve more for rabble than for elites.
    Situation wounded;
    wounded.health = 0.1F;
    assert(Think(Grunt(), wounded).confidenceShift < Think(Grunt(), {}).confidenceShift);

    // For Honor wins: a weapon master is Elite even at low level, and never gets Dynamic Grip.
    Profile master = Grunt();
    master.master = true;
    assert(Think(master, {}).tier == Tier::Elite);
    assert(Think(master, {}).confidenceShift > Think(Grunt(), {}).confidenceShift);
    assert(!GripSchooled(Think(master, {}).tier, master.doctrine, master.master));
    assert(GripSchooled(Think(Legend(), {}).tier, Doctrine::Military, false));

    // A For Honor master is blocked from Dynamic Grip whether or not the grip option is on (3.0.3-3.0.5 released
    // the master's keyword again as soon as the option was off).
    assert(GripBlockWanted(false, Tier::Elite, Doctrine::Bandit, true));
    assert(GripBlockWanted(true, Tier::Elite, Doctrine::Bandit, true));
    // Option off: nobody else is blocked. Option on: only the unschooled and casters are.
    assert(!GripBlockWanted(false, Tier::Rabble, Doctrine::Bandit, false));
    assert(GripBlockWanted(true, Tier::Rabble, Doctrine::Bandit, false));
    assert(!GripBlockWanted(true, Tier::Trained, Doctrine::Bandit, false));
    assert(GripBlockWanted(true, Tier::Elite, Doctrine::Caster, false));

    // A temporary effect on top of the permanent value changes neither the authored base nor the wanted shift.
    {
        const float authored = 3.0F, applied = 1.0F, fear = -4.0F;
        const float permanent = authored + applied;           // what GetPermanentActorValue reports
        const float current = permanent + fear;               // what GetActorValue reports while feared
        assert(std::fabs(AuthoredBase(permanent, applied) - authored) < 1e-5F);
        assert(AuthoredBase(current, applied) < 0.0F);        // the old reading: a base that never existed
        const float base = AuthoredBase(permanent, applied);
        assert(std::fabs((ClampConfidence(base + 1.0F) - base) - applied) < 1e-5F);  // no extra write under fear
    }

    // Dynamic Grip is for schooled non-casters only.
    assert(!GripSchooled(Tier::Rabble, Doctrine::Bandit, false));
    assert(GripSchooled(Tier::Trained, Doctrine::Bandit, false));
    assert(!GripSchooled(Tier::Elite, Doctrine::Caster, false));

    // Pool slot is stable per NPC and uses both slots.
    assert(PoolSlot(0x10) != PoolSlot(0x20));
    assert(PoolSlot(0x1234) == PoolSlot(0x1234));

    // Non-finite and out-of-range inputs stay bounded and quantized.
    Profile bad = Grunt();
    bad.level = std::nanf("");
    bad.skill = -50.0F;
    Situation weird;
    weird.health = std::nanf("");
    weird.foeLevel = 1e9F;
    const Mind m = Think(bad, weird);
    assert(std::isfinite(m.intellect) && std::fabs(m.confidenceShift) <= 2.5F);
    assert(std::fmod(std::fabs(m.confidenceShift) * 4.0F, 1.0F) == 0.0F);

    // ---- modifier contract: signed application, reversal, idempotence, boundaries ----
    // v1 records came from builds that applied |delta| on the damage channel; they are not replayable.
    assert(!RestorableCoSave(kLegacyCoSaveVersion));
    assert(RestorableCoSave(kCoSaveVersion));
    assert(RestorableCoSave(kCoSaveVersion + 1));

    // A permanent shift moves the value one way, and its revert moves it back - signs must be opposite.
    {
        float authored = 2.0F;
        float applied = 0.0F;
        const float shift = -0.75F;
        // apply
        float current = authored + shift;
        applied = shift;
        // revert
        current += RevertDelta(applied);
        applied = 0.0F;
        assert(std::fabs(current - authored) < 1e-4F);
        assert(std::fabs(RevertDelta(-0.75F) - 0.75F) < 1e-6F);
    }

    // Positive and negative shifts move in opposite directions (the 3.0.1/3.0.2 bug applied both as a penalty).
    {
        const float authored = 2.0F;
        const float up = ClampConfidence(authored + 1.25F);   // 3.25
        const float down = ClampConfidence(authored - 1.25F); // 0.75
        assert(up > authored && down < authored);
    }

    // Reading the authored value back through our own delta and re-deciding the same shift must not add anything.
    {
        const float authored = 1.5F;
        float applied = -0.5F;
        const float current = authored + applied;
        const float base = AuthoredBase(current, applied);
        assert(std::fabs(base - authored) < 1e-5F);
        const float wanted = ClampConfidence(base - 0.5F) - base;
        assert(std::fabs(wanted - applied) < 1e-5F);  // same target: no further write
    }

    // Boundaries: a -2.5 shift on a low value stops at 0, a +2.5 shift on a high value stops at 4.
    {
        const float lowBase = 0.25F;
        const float lowWanted = ClampConfidence(lowBase - 2.5F) - lowBase;
        assert(std::fabs(lowWanted + 0.25F) < 1e-5F);
        const float highBase = 3.75F;
        const float highWanted = ClampConfidence(highBase + 2.5F) - highBase;
        assert(std::fabs(highWanted - 0.25F) < 1e-5F);
        assert(ClampConfidence(-1.0F) == 0.0F);
        assert(ClampConfidence(9.0F) == 4.0F);
    }

    // ---- grading state across worlds (the 3.0.4 sentinel bug in transition form) ----
    {
        GradeState st;
        assert(st.NeedsPass(0));          // first world of the process is generation 0 and must be graded
        st.Recorded(0);
        assert(!st.NeedsPass(0));         // same world: no second pass
        assert(st.NeedsPass(1));          // new world: grade again
        st.Reset();                       // styles restored (option off / world change)
        assert(st.NeedsPass(0));          // and retryable in the same world afterwards
    }
    {
        // A pass that could not run (missing styles plugin) records nothing, so it stays retryable.
        GradeState st;
        const bool ran = false;
        if (ran) st.Recorded(0);
        assert(st.NeedsPass(0));
        st.Recorded(0);
        assert(!st.NeedsPass(0));
        st.Recorded(0);                   // repeated record is harmless
        assert(!st.NeedsPass(0));
        assert(st.NeedsPass(2));          // save A -> save B
        st.Recorded(2);
        assert(!st.NeedsPass(2));
        assert(st.NeedsPass(1));          // back to save A's world still needs its own pass
    }

    // ---- Dynamic Grip ownership ledger ----
    {
        // A For Honor master that already carried the keyword: nothing of ours to remove, ledger still ends clean.
        GripLedger g;
        assert(g.ReleaseAll().empty());
        assert(g.blocked.empty());
        // Repeat release on an already-clean ledger does nothing harmful.
        assert(g.ReleaseAll().empty());
    }
    {
        GripLedger g;
        g.Block(10);
        g.Block(20);
        assert(g.OwnedByUs(10));
        const auto owned = g.ReleaseAll();
        assert(owned.size() == 2);
        assert(g.blocked.empty() && !g.OwnedByUs(10));
        assert(g.ReleaseAll().empty());
    }
    {
        // One base ours, another only seen as a master: release returns only ours and clears the ledger.
        GripLedger g;
        g.Block(0xAAA);
        const auto owned = g.ReleaseAll();
        assert(owned.size() == 1 && owned[0] == 0xAAA);
        assert(g.blocked.empty());
    }
    {
        // Taking a keyword back one base at a time (keyword was taken off by another mod) keeps the ledger honest.
        GripLedger g;
        g.Block(5);
        assert(g.TakeBack(5));
        assert(!g.TakeBack(5));
        assert(!g.OwnedByUs(5));
        assert(g.ReleaseAll().empty());
    }
    // A keyword is ours to remove only when we added it and it is still present.
    assert(OwnsKeyword(true, true));
    assert(!OwnsKeyword(true, false));   // another mod or the console removed it
    assert(!OwnsKeyword(false, true));   // a foreign keyword we never added

#ifdef NCAI_SELFTEST_FAIL
    assert(false && "self-test: assertions are live");
#endif
    std::puts("policy_tests passed");
    return 0;
}
