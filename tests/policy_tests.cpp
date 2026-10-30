// Host checks for the combat-mind policy; asserts stay active in release builds (/UNDEBUG).
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

    std::puts("policy_tests passed");
    return 0;
}
