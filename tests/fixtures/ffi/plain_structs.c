typedef struct { int x; int y; } Point;
Point point_add(Point a, Point b) { Point r = {a.x + b.x, a.y + b.y}; return r; }
double point_dot(Point a, Point b) { return (double)a.x * b.x + (double)a.y * b.y; }
