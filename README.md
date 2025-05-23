# The Valiance Programming Language

Array languages are cool, but horribly unoptimised for mainstream usage.
Valiance rectifies this by providing a stack-based array language
that has been designed with mainstream appeal in mind.

It is boring compared to other array languages, but that's the point. We don't
need production code to look like a hex dump experiment, nor does it need to
be something that is an "adventure". It just needs to work. Valiance does that.

## But Where's the Code?

Right now, I'm going for a python implementation of Valiance. I tried doing a scala project, but metals just wasn't playing nice. Additionally, while Valiance will need to be ported to something faster at some point, I think it's worth creating a quick and dirty proof of concept to demonstrate language features instead of going fast. 