ALGORITHMS:=adaptive
DIRS?= subproblems
INPUT:=$(sort $(foreach DIR,$(DIRS),$(wildcard $(DIR)/*)))
OUTPUT:=$(sort $(foreach alg,$(ALGORITHMS),$(addsuffix -$(alg),$(addprefix output/,$(INPUT)))))

output/%-dphyp: %
	@mkdir -p $(dir $@)
	../bin/dp dphyp $@ $<

output/%-dpsize: %
	@mkdir -p $(dir $@)
	../bin/dp dpsize $@ $<

output/%-dpsizelinear: %
	@mkdir -p $(dir $@)
	../bin/dp dpsizelinear $@ $<

output/%-ikkbz: %
	@mkdir -p $(dir $@)
	../bin/dp ikkbz $@ $<

output/%-ikkbzbushy: %
	@mkdir -p $(dir $@)
	../bin/dp ikkbzbushy $@ $<

output/%-goo: %
	@mkdir -p $(dir $@)
	../bin/dp goo $@ $<

output/%-goodp: %
	@mkdir -p $(dir $@)
	../bin/dp goodp $@ $<

output/%-goodp2: %
	@mkdir -p $(dir $@)
	../bin/dp goodp2 $@ $<

output/%-gooikkbz: %
	@mkdir -p $(dir $@)
	../bin/dp gooikkbz $@ $<

output/%-quickpick: %
	@mkdir -p $(dir $@)
	../bin/dp quickpick $@ $<

output/%-genetic: %
	@mkdir -p $(dir $@)
	../bin/dp genetic $@ $<

output/%-simplification: %
	@mkdir -p $(dir $@)
	../bin/dp simplification $@ $<

output/%-adaptive: %
	@mkdir -p $(dir $@)
	../bin/dp adaptive $@ $<

output/%-minsel: %
	@mkdir -p $(dir $@)
	../bin/dp minsel $@ $<

all: $(OUTPUT)
