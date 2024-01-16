#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "structmember.h"
#include "novaphysics/novaphysics.h"


#define NOVA_PYTHON_VERSION "0.0.2"



/*  #######################################################

                         Object Interfaces

    #######################################################  */



/**
 * Vector2 object interface
 */
typedef struct {
    PyObject_HEAD
    double x;
    double y;
} nvVector2Object;

/**
 * Body object interface
 */
typedef struct {
    PyObject_HEAD
    nvBody *body;
    nvBodyType type;
    int shape;
    nvVector2Object *position;
    double angle;
    double radius;
    nv_uint16 id;
} nvBodyObject;

/**
 * Space object interface
 */
typedef struct {
    PyObject_HEAD
    nvSpace *space;
    nvArray *body_objects;
} nvSpaceObject;

/**
 * Distance Joint Constraint object interface
 */
typedef struct {
    PyObject_HEAD
    nvConstraint *cons;
    double length;
} nvDistanceJointObject;



/*  #######################################################

                          Vector2

    #######################################################  */



/**
 * Create new Vector2 object
 */
nvVector2Object *nvVector2Object_new(double x, double y);

/**
 * Vector2 Python object to Vector2 struct
 */
#define PY_TO_VEC2(o) (NV_VEC2((o)->x, (o)->y))



static void nvVector2Object_dealloc(nvVector2Object *self) {
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static int nvVector2Object_init(
    nvVector2Object *self,
    PyObject *args,
    PyObject *kwds
) {
    double x;
    double y;

    if (!PyArg_ParseTuple(args, "dd", &x, &y))
        return -1;

    self->x = x;
    self->y = y;

    return 0;
}


static PyObject *nvVector2Object___repr__(nvVector2Object* self) {
    return PyUnicode_FromFormat("<Vector2(%g, %g)>", self->x, self->y);
}


/**
 * Vector2 object method interface
 */
static PyMethodDef nvVector2Object_methods[] = {
    {
        "__repr__",
        (PyCFunction)nvVector2Object___repr__, METH_NOARGS,
        ""
    },

    {NULL} // Sentinel
};

static PyObject *nvVector2Object___add__(
    nvVector2Object *self,
    nvVector2Object *vector
) {
    nvVector2 result = nvVector2_add(PY_TO_VEC2(self), PY_TO_VEC2(vector));

    return nvVector2Object_new(result.x, result.y);
}

static PyObject *nvVector2Object___sub__(
    nvVector2Object *self,
    nvVector2Object *vector
) {
    nvVector2 result = nvVector2_sub(PY_TO_VEC2(self), PY_TO_VEC2(vector));

    return nvVector2Object_new(result.x, result.y);
}

static PyObject *nvVector2Object___mul__(
    nvVector2Object *self,
    PyObject *scalar
) {
    double s = PyFloat_AS_DOUBLE(scalar);

    nvVector2 result = nvVector2_mul(PY_TO_VEC2(self), s);

    return nvVector2Object_new(result.x, result.y);
}

static PyObject *nvVector2Object___truediv__(
    nvVector2Object *self,
    PyObject *scalar
) {
    double s = PyFloat_AS_DOUBLE(scalar);

    nvVector2 result = nvVector2_div(PY_TO_VEC2(self), s);

    return nvVector2Object_new(result.x, result.y);
}

/**
 * Vector2 object operator overloadings
 */
static PyNumberMethods nvVector2Object_operators = {
    .nb_add =         (binaryfunc)nvVector2Object___add__,
    .nb_subtract =    (binaryfunc)nvVector2Object___sub__,
    .nb_multiply =    (binaryfunc)nvVector2Object___mul__,
    .nb_true_divide = (binaryfunc)nvVector2Object___truediv__
};

/**
 * Vector2 object member interface
 */
static PyMemberDef nvVector2Object_members[] = {
    {
        "x",
        T_DOUBLE, offsetof(nvVector2Object, x), 0,
        ""
    },

    {
        "y",
        T_DOUBLE, offsetof(nvVector2Object, y), 0,
        ""
    },

    {NULL} // Sentinel
};

/**
 * Vector2 object type internals
 */
PyTypeObject nvVector2ObjectType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "nova.Vector2",
    .tp_doc = "Vector2 object",
    .tp_basicsize = sizeof(nvVector2Object),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = PyType_GenericNew,
    .tp_dealloc = (destructor)nvVector2Object_dealloc,
    .tp_init = (initproc)nvVector2Object_init,
    .tp_members = nvVector2Object_members,
    .tp_as_number = &nvVector2Object_operators,
    .tp_str = (reprfunc)nvVector2Object___repr__
};

nvVector2Object *nvVector2Object_new(double x, double y) {
    PyObject *args = Py_BuildValue("dd", x, y);
    nvVector2Object *obj = (nvVector2Object *)PyObject_CallObject((PyObject *)&nvVector2ObjectType, args);
    Py_DECREF(args);
    Py_INCREF(obj);
    return obj;
}



/*  #######################################################

                             Body

    #######################################################  */



static void nvBodyObject_dealloc(nvBodyObject *self) {
    // Don't free nvBody instance because space frees it
    Py_XDECREF(self->position);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static int nvBodyObject_init(
    nvBodyObject *self,
    PyObject *args,
    PyObject *kwds
) {
    nvBodyType type;
    int shape;
    double x;
    double y;
    double angle;
    double density;
    double restitution;
    double friction;
    double radius;
    PyObject *vertices = NULL;
    int hull = false;

    if (!PyArg_ParseTuple(
        args, "iiddddddd|Oi",
        &type, &shape, &x, &y, &angle, &density, &restitution, &friction, &radius, &vertices, &hull
    ))
        return -1;

    self->type = type;
    self->shape = shape;
    self->position = (nvVector2Object *)nvVector2Object_new(x, y);
    self->angle = angle;
    self->radius = radius;

    nvArray *new_vertices = NULL;

    // Validate polygon vertices
    if (vertices) {
        if (!PySequence_Check(vertices)) {
            PyErr_SetString(PyExc_TypeError, "Vertices must be a sequence of number pairs");
            return 0;
        }

        size_t vertices_len = PySequence_Length(vertices);

        if (vertices_len < 3) {
            PyErr_SetString(PyExc_ValueError, "Polygon vertices must be at least length of 3");
            return 0;
        }

        // Create nvArray from vertices sequence
        new_vertices = nvArray_new();
        PyObject *v;
        PyObject *vx;
        PyObject *vy;

        for (size_t i = 0; i < vertices_len; i++) {
            v = PySequence_GetItem(vertices, i);
            vx = PySequence_GetItem(v, 0);
            vy = PySequence_GetItem(v, 1);

            nvArray_add(new_vertices, NV_VEC2_NEW(PyFloat_AS_DOUBLE(vx), PyFloat_AS_DOUBLE(vy)));

            Py_DECREF(v);
            Py_DECREF(vx);
            Py_DECREF(vy);
        }
    }

    if (shape == 0) {
        self->body = nvBody_new(
            type,
            nvCircleShape_new(radius),
            NV_VEC2(x, y),
            angle,
            (nvMaterial){density, restitution, friction}
        );
    }

    else if (shape == 1) {
        if (hull) {
            nvShape *convex_hull_shape = nvConvexHullShape_new(new_vertices);

            self->body = nvBody_new(
                type,
                convex_hull_shape,
                NV_VEC2(x, y),
                angle,
                (nvMaterial){density, restitution, friction}
            );
        }
        else {
            self->body = nvBody_new(
                type,
                nvPolygonShape_new(new_vertices),
                NV_VEC2(x, y),
                angle,
                (nvMaterial){density, restitution, friction}
            );
        }
    }

    // Actual ID is assigned at adding to space
    self->id = 0;

    return 0;
}

/**
 * Body object member interface
 */
static PyMemberDef nvBodyObject_members[] = {
    {
        "type",
        T_INT, offsetof(nvBodyObject, type), 0,
        ""
    },

    {
        "shape",
        T_INT, offsetof(nvBodyObject, shape), 0,
        ""
    },

    {
        "position",
        T_OBJECT_EX, offsetof(nvBodyObject, position), 0,
        ""
    },

    {
        "angle",
        T_DOUBLE, offsetof(nvBodyObject, angle), 0,
        ""
    },

    {
        "radius",
        T_DOUBLE, offsetof(nvBodyObject, radius), 0,
        ""
    },

    {
        "id",
        T_INT, offsetof(nvBodyObject, id), 0,
        ""
    },

    {NULL} // Sentinel
};

static PyObject *nvBodyObject_get_vertices(
    nvBodyObject *self,
    PyObject *Py_UNUSED(ignored)
) {
    nvBody_local_to_world(self->body);
    PyObject *return_tup = PyTuple_New(self->body->shape->trans_vertices->size);

    for (size_t i = 0; i < self->body->shape->trans_vertices->size; i++) {
        nvVector2 v = NV_TO_VEC2(self->body->shape->trans_vertices->data[i]);

        PyTuple_SET_ITEM(return_tup, i, (PyObject *)nvVector2Object_new(v.x, v.y));
    }

    return return_tup;
}

static PyObject *nvBodyObject_get_aabb(
    nvBodyObject *self,
    PyObject *Py_UNUSED(ignored)
) {
    PyObject *return_tup = PyTuple_New(4);

    nvAABB aabb = nvBody_get_aabb(self->body);

    PyTuple_SET_ITEM(return_tup, 0, PyFloat_FromDouble(aabb.min_x));
    PyTuple_SET_ITEM(return_tup, 1, PyFloat_FromDouble(aabb.min_y));
    PyTuple_SET_ITEM(return_tup, 2, PyFloat_FromDouble(aabb.max_x));
    PyTuple_SET_ITEM(return_tup, 3, PyFloat_FromDouble(aabb.max_y));

    return return_tup;
}

static PyObject *nvBodyObject_apply_force(
    nvBodyObject *self,
    PyObject *args
) {
    nvVector2Object *force;

    if (!PyArg_ParseTuple(args, "O!", &nvVector2ObjectType, &force))
        return NULL;

    nvBody_apply_force(self->body, NV_VEC2(force->x, force->y));

    Py_RETURN_NONE;
}

static PyObject *nvBodyObject_apply_force_at(
    nvBodyObject *self,
    PyObject *args
) {
    nvVector2Object *force;
    nvVector2Object *position;

    if (!PyArg_ParseTuple(args, "O!O!", &nvVector2ObjectType, &force, &nvVector2ObjectType, &position))
        return NULL;

    nvBody_apply_force_at(self->body, NV_VEC2(force->x, force->y), NV_VEC2(position->x, position->y));

    Py_RETURN_NONE;
}

static PyObject *nvBodyObject_apply_torque(
    nvBodyObject *self,
    PyObject *args
) {
    double torque;

    if (!PyArg_ParseTuple(args, "d", &torque))
        return NULL;

    self->body->torque += torque;

    Py_RETURN_NONE;
}

static PyObject *nvBodyObject_apply_impulse(
    nvBodyObject *self,
    PyObject *args
) {
    nvVector2Object *force;
    nvVector2Object *position;

    if (!PyArg_ParseTuple(args, "O!O!", &nvVector2ObjectType, &force, &nvVector2ObjectType, &position))
        return NULL;

    nvBody_apply_impulse(self->body, NV_VEC2(force->x, force->y), NV_VEC2(position->x, position->y));

    Py_RETURN_NONE;
}

static PyObject *nvBodyObject_set_inertia(
    nvBodyObject *self,
    PyObject *args
) {
    double inertia;

    if (!PyArg_ParseTuple(args, "d", &inertia))
        return NULL;

    nvBody_set_inertia(self->body, inertia);

    Py_RETURN_NONE;
}

static PyObject *nvBodyObject_get_inertia(
    nvBodyObject *self,
    PyObject *Py_UNUSED(ignored)
) {
    return PyFloat_FromDouble(self->body->inertia);
}

static PyObject *nvBodyObject_set_position(
    nvBodyObject *self,
    PyObject *args
) {
    nvVector2Object *position;

    if (!PyArg_ParseTuple(args, "O!", &nvVector2ObjectType, &position))
        return NULL;

    self->body->position = NV_VEC2(position->x, position->y);
    self->position->x = self->body->position.x;
    self->position->y = self->body->position.y; 

    Py_RETURN_NONE;
}

static PyObject *nvBodyObject_enable_collision(
    nvBodyObject *self,
    PyObject *args
) {
    unsigned char collision;

    if (!PyArg_ParseTuple(args, "b", &collision))
        return NULL;

    self->body->enable_collision = collision;

    Py_RETURN_NONE;
}

static PyObject *nvBodyObject_get_collision_group(
    nvBodyObject *self,
    PyObject *Py_UNUSED(ignored)
) {
    return PyBool_FromLong((long)self->body->collision_group);
}

static PyObject *nvBodyObject_set_collision_group(
    nvBodyObject *self,
    PyObject *args
) {
    int group;

    if (!PyArg_ParseTuple(args, "i", &group))
        return NULL;

    self->body->collision_group = group;

    Py_RETURN_NONE;
}

/**
 * Body object method interface
 */
static PyMethodDef nvBodyObject_methods[] = {
    {
        "get_vertices",
        (PyCFunction)nvBodyObject_get_vertices, METH_NOARGS,
        ""
    },

    {
        "get_aabb",
        (PyCFunction)nvBodyObject_get_aabb, METH_NOARGS,
        ""
    },

    {
        "apply_force",
        (PyCFunction)nvBodyObject_apply_force, METH_VARARGS,
        ""
    },

    {
        "apply_force_at",
        (PyCFunction)nvBodyObject_apply_force_at, METH_VARARGS,
        ""
    },

    {
        "apply_torque",
        (PyCFunction)nvBodyObject_apply_torque, METH_VARARGS,
        ""
    },

    {
        "apply_impulse",
        (PyCFunction)nvBodyObject_apply_impulse, METH_VARARGS,
        ""
    },

    {
        "set_inertia",
        (PyCFunction)nvBodyObject_set_inertia, METH_VARARGS,
        ""
    },

    {
        "get_inertia",
        (PyCFunction)nvBodyObject_get_inertia, METH_NOARGS,
        ""
    },

    {
        "set_position",
        (PyCFunction)nvBodyObject_set_position, METH_VARARGS,
        ""
    },

    {
        "enable_collision",
        (PyCFunction)nvBodyObject_enable_collision, METH_VARARGS,
        ""
    },

    {
        "get_collision_group",
        (PyCFunction)nvBodyObject_get_collision_group, METH_NOARGS,
        ""
    },

    {
        "set_collision_group",
        (PyCFunction)nvBodyObject_set_collision_group, METH_VARARGS,
        ""
    },

    {NULL} // Sentinel
};

static PyObject *nvBodyObject_get_mass(nvBodyObject *self, void *closure) {
    return PyFloat_FromDouble(self->body->mass);
}

static int nvBodyObject_set_mass(nvBodyObject *self, PyObject *value, void *closure) {
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete the property.");
        return -1;
    }

    if (!PyFloat_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "Value must be a float.");
        return -1;
    }

    nvBody_set_mass(self->body, PyFloat_AS_DOUBLE(value));

    return 0;
}

/**
 * Body object property interface
 */
static PyGetSetDef nvBodyObject_properties[] = {
    {
        "mass",
        (getter)nvBodyObject_get_mass, (setter)nvBodyObject_set_mass,
        "", NULL
    },

    {NULL}  // Sentinel
};

PyTypeObject nvBodyObjectType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "nova.Body",
    .tp_doc = "Body object",
    .tp_basicsize = sizeof(nvBodyObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = PyType_GenericNew,
    .tp_dealloc = (destructor)nvBodyObject_dealloc,
    .tp_init = (initproc)nvBodyObject_init,
    .tp_methods = nvBodyObject_methods,
    .tp_members = nvBodyObject_members,
    .tp_getset = nvBodyObject_properties
};


PyObject *nv_create_circle(PyObject *self, PyObject *args) {
    nvBodyType type;
    double x;
    double y;
    double angle;
    double density;
    double restitution;
    double friction;
    double radius;

    if (!PyArg_ParseTuple(
        args, "iddddddd",
        &type, &x, &y, &angle, &density, &restitution, &friction, &radius
    ))
        return NULL;

    PyObject *inst_args = Py_BuildValue("iiddddddd", type, 0, x, y, angle, density, restitution, friction, radius);
    nvBodyObject *obj = (nvBodyObject *)PyObject_CallObject((PyObject *)&nvBodyObjectType, inst_args);
    Py_DECREF(inst_args);
    return (PyObject *)obj;
}

PyObject *nv_create_rect(PyObject *self, PyObject *args) {
    nvBodyType type;
    double x;
    double y;
    double angle;
    double density;
    double restitution;
    double friction;
    double width;
    double height;

    if (!PyArg_ParseTuple(
        args, "idddddddd",
        &type, &x, &y, &angle, &density, &restitution, &friction, &width, &height
    ))
        return NULL;

    double w = width / 2.0;
    double h = height / 2.0;

    PyObject *inst_args = Py_BuildValue("iiddddddd((dd)(dd)(dd)(dd))", type, 1, x, y, angle, density, restitution, friction, 0.0,
        -w, -h, w, -h, w, h, -w, h);

    nvBodyObject *obj = (nvBodyObject *)PyObject_CallObject((PyObject *)&nvBodyObjectType, inst_args);
    Py_DECREF(inst_args);
    return (PyObject *)obj;
}

PyObject *nv_create_polygon(PyObject *self, PyObject *args) {
    nvBodyType type;
    double x;
    double y;
    double angle;
    double density;
    double restitution;
    double friction;
    PyObject *vertices;
    int hull = false;

    if (!PyArg_ParseTuple(
        args, "iddddddO|i",
        &type, &x, &y, &angle, &density, &restitution, &friction, &vertices, &hull
    ))
        return NULL;

    if (!PySequence_Check(vertices)) {
        PyErr_SetString(PyExc_TypeError, "Vertices must be a sequence of number pairs");
        return 0;
    }

    size_t vertices_len = PySequence_Length(vertices);

    if (vertices_len < 3) {
        PyErr_SetString(PyExc_ValueError, "Polygon vertices must be at least length of 3");
        return 0;
    }

    PyObject *inst_args = Py_BuildValue("iidddddddOi", type, 1, x, y, angle, density, restitution, friction, 0.0, vertices, hull);
    nvBodyObject *obj = (nvBodyObject *)PyObject_CallObject((PyObject *)&nvBodyObjectType, inst_args);
    Py_DECREF(inst_args);
    return (PyObject *)obj;
}



/*  #######################################################

                  Distance Join Constraint

    #######################################################  */



static void nvDistanceJointObject_dealloc(nvDistanceJointObject *self) {
    // Don't free constraint ecause space frees it
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static int nvDistanceJointObject_init(
    nvDistanceJointObject *self,
    PyObject *args,
    PyObject *kwds
) {
    nvBodyType type;
    int shape;
    double x;
    double y;
    double angle;
    double density;
    double restitution;
    double friction;
    double radius;
    PyObject *vertices = NULL;

    nvBodyObject *a = NULL;
    nvBodyObject *b = NULL;
    nvVector2Object *anchor_a = NULL;
    nvVector2Object *anchor_b = NULL;
    double length;

    if (!PyArg_ParseTuple(
        args, "O!O!O!O!d",
        &nvBodyObjectType, &a,
        &nvBodyObjectType, &b,
        &nvVector2ObjectType, &anchor_a,
        &nvVector2ObjectType, &anchor_b,
        &length
    ))
        return -1;
    
    self->cons = nvDistanceJoint_new(
        a->body, b->body, PY_TO_VEC2(anchor_a), PY_TO_VEC2(anchor_b), length
    );

    return 0;
}

/**
 * Distance joint object member interface
 */
static PyMemberDef nvDistanceJointObject_members[] = {
    {
        "length",
        T_DOUBLE, offsetof(nvDistanceJointObject, length), 0,
        ""
    },

    {NULL} // Sentinel
};

PyTypeObject nvDistanceJointObjectType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "nova.DistanceJoint",
    .tp_doc = "Distance joint constraintt",
    .tp_basicsize = sizeof(nvDistanceJointObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = PyType_GenericNew,
    .tp_dealloc = (destructor)nvDistanceJointObject_dealloc,
    .tp_init = (initproc)nvDistanceJointObject_init,
    .tp_members = nvDistanceJointObject_members
};



/*  #######################################################

                            Space

    #######################################################  */



static void nvSpaceObject_dealloc(nvSpaceObject *self) {
    nvSpace_free(self->space);

    // Decrease reference of each body object in array
    for (size_t i = 0; i < self->body_objects->size; i++) {
        PyObject *body = (PyObject *)self->body_objects->data[i];
        Py_DECREF(body);
    }

    nvArray_free(self->body_objects);

    Py_TYPE(self)->tp_free((PyObject *) self);
}

static int nvSpaceObject_init(
    nvSpaceObject *self,
    PyObject *args,
    PyObject *kwds
) {
    self->space = nvSpace_new();
    self->body_objects = nvArray_new();

    return 0;
}

static PyObject *nvSpaceObject_step(
    nvSpaceObject *self,
    PyObject *args
) {
    double dt;
    int velocity_iters;
    int position_iters;
    int constraint_iters;
    int substeps;

    if (!PyArg_ParseTuple(
            args, "diiii",
            &dt,
            &velocity_iters,
            &position_iters,
            &constraint_iters,
            &substeps
    )) return NULL;

    nvSpace_step(
        self->space,
        dt,
        velocity_iters,
        position_iters,
        constraint_iters,
        substeps
    );

    nvArray *removed = nvArray_new();

    for (size_t i = 0; i < self->body_objects->size; i++) {
        nvBodyObject *body_object = (nvBodyObject *)self->body_objects->data[i];

        bool found = false;
        nvBody *found_body;
        for (size_t j = 0; j < self->space->bodies->size; j++) {
            nvBody *body = (nvBody *)self->space->bodies->data[j];
            if (body == body_object->body) {
                found = true;
                found_body = body;
                break;
            }
        }

        if (!found) {
            nvArray_add(removed, body_object);
            continue;
        }

        Py_INCREF(body_object);
        
        body_object->position->x = found_body->position.x;
        body_object->position->y = found_body->position.y;
        body_object->angle = found_body->angle;
        body_object->radius = found_body->shape->radius;

        Py_DECREF(body_object);
    }

    for (size_t i = 0; i < removed->size; i++) {
        nvBodyObject *body_object = removed->data[i];
        Py_DECREF(body_object);
        nvArray_remove(self->body_objects, body_object);
    }

    Py_RETURN_NONE;
}

static PyObject *nvSpaceObject_get_bodies(
    nvSpaceObject *self,
    PyObject *Py_UNUSED(ignored)
) {
    PyObject *return_tup = PyTuple_New(self->body_objects->size);

    for (size_t i = 0; i < self->body_objects->size; i++) {
        nvBodyObject *body = (nvBodyObject *)self->body_objects->data[i];
        
        Py_INCREF(body);
        PyTuple_SET_ITEM(return_tup, i, body);
    }

    return return_tup;
}

static PyObject *nvSpaceObject_get_constraints(
    nvSpaceObject *self,
    PyObject *Py_UNUSED(ignored)
) {
    size_t n = self->space->constraints->size;

    PyObject *return_tup = PyTuple_New(n);

    for (size_t i = 0; i < n; i++) {
        nvConstraint *cons = self->space->constraints->data[i];

        if (cons->type == nvConstraintType_DISTANCEJOINT) {
            // Transform distance joint's anchors to world space
            nvVector2 ra = nvVector2_add(nvVector2_rotate(((nvDistanceJoint *)cons->def)->anchor_a, cons->a->angle), cons->a->position);
            nvVector2 rb = nvVector2_add(nvVector2_rotate(((nvDistanceJoint *)cons->def)->anchor_b, cons->b->angle), cons->b->position);

            PyObject *cons_tup = PyTuple_New(3);
            PyTuple_SET_ITEM(cons_tup, 0, PyLong_FromLong(1)); // 1 -> distance joint
            PyTuple_SET_ITEM(cons_tup, 1, nvVector2Object_new(ra.x, ra.y));
            PyTuple_SET_ITEM(cons_tup, 2, nvVector2Object_new(rb.x, rb.y));
            
            PyTuple_SET_ITEM(return_tup, i, cons_tup);
        }
        else {
            PyObject *cons_tup = PyTuple_New(3);
            PyTuple_SET_ITEM(cons_tup, 0, PyLong_FromLong(0));
            PyTuple_SET_ITEM(cons_tup, 1, PyLong_FromLong(0));
            PyTuple_SET_ITEM(cons_tup, 2, PyLong_FromLong(0));

            PyTuple_SET_ITEM(return_tup, i, cons_tup);
        }
    }

    return return_tup;
}

static PyObject *nvSpaceObject_add(
    nvSpaceObject *self,
    PyObject *args
) {
    nvBodyObject *body;

    if (!PyArg_ParseTuple(args, "O!", &nvBodyObjectType, &body))
        return NULL;

    nvSpace_add(self->space, body->body);
    body->id = body->body->id;
    Py_INCREF(body);
    nvArray_add(self->body_objects, body);

    Py_RETURN_NONE;
}

static PyObject *nvSpaceObject_add_constraint(
    nvSpaceObject *self,
    PyObject *args
) {
    PyObject *constraint;

    if (!PyArg_ParseTuple(args, "O", &constraint))
        return NULL;

    if (PyObject_IsInstance(constraint, (PyObject *)(&nvDistanceJointObjectType)))
        nvSpace_add_constraint(self->space, ((nvDistanceJointObject *)constraint)->cons);

    Py_RETURN_NONE;
}

static PyObject *nvSpaceObject_remove(
    nvSpaceObject *self,
    PyObject *args
) {
    nvBodyObject *body;

    if (!PyArg_ParseTuple(args, "O!", &nvBodyObjectType, &body))
        return NULL;

    nvSpace_remove(self->space, body->body);
    nvArray_remove(self->body_objects, body);
    Py_XDECREF(body);

    Py_RETURN_NONE;
}

static PyObject *nvSpaceObject_clear(
    nvSpaceObject *self,
    PyObject *Py_UNUSED(ignored)
) {
    while (self->body_objects->size > 0) {
        nvBodyObject *body_obj = (nvBodyObject *)nvArray_pop(self->body_objects, 0);
        Py_DECREF(body_obj);
    }

    nvSpace_clear(self->space);

    Py_RETURN_NONE;
}

static PyObject *nvSpaceObject_set_shg(
    nvSpaceObject *self,
    PyObject *args
) {
    double min_x;
    double min_y;
    double max_x;
    double max_y;
    double cell_width;
    double cell_height;

    if (!PyArg_ParseTuple(args, "dddddd", &min_x, &min_y, &max_x, &max_y, &cell_width, &cell_height))
        return NULL;

    nvSpace_set_SHG(
        self->space,
        (nvAABB){min_x, min_y, max_x, max_y},
        cell_width,
        cell_height
    );

    Py_RETURN_NONE;
}

static PyObject *nvSpaceObject_get_shg(
    nvSpaceObject *self,
    PyObject *Py_UNUSED(ignored)
) {
    PyObject *return_tup = PyTuple_New(6);

    PyTuple_SET_ITEM(return_tup, 0, PyFloat_FromDouble(self->space->shg->bounds.min_x));
    PyTuple_SET_ITEM(return_tup, 1, PyFloat_FromDouble(self->space->shg->bounds.min_y));
    PyTuple_SET_ITEM(return_tup, 2, PyFloat_FromDouble(self->space->shg->bounds.max_x));
    PyTuple_SET_ITEM(return_tup, 3, PyFloat_FromDouble(self->space->shg->bounds.max_y));
    PyTuple_SET_ITEM(return_tup, 4, PyFloat_FromDouble(self->space->shg->cell_width));
    PyTuple_SET_ITEM(return_tup, 5, PyFloat_FromDouble(self->space->shg->cell_height));

    return return_tup;
}

static PyObject *nvSpaceObject_set_kill_bounds(
    nvSpaceObject *self,
    PyObject *args
) {
    double min_x;
    double min_y;
    double max_x;
    double max_y;

    if (!PyArg_ParseTuple(args, "dddd", &min_x, &min_y, &max_x, &max_y))
        return NULL;

    self->space->kill_bounds = (nvAABB){min_x, min_y, max_x, max_y};

    Py_RETURN_NONE;
}

/**
 * Space object method interface
 */
static PyMethodDef nvSpaceObject_methods[] = {
    {
        "step",
        (PyCFunction)nvSpaceObject_step, METH_VARARGS,
        ""
    },

    {
        "get_bodies",
        (PyCFunction)nvSpaceObject_get_bodies, METH_NOARGS,
        ""
    },

    {
        "get_constraints",
        (PyCFunction)nvSpaceObject_get_constraints, METH_NOARGS,
        ""
    },

    {
        "add",
        (PyCFunction)nvSpaceObject_add, METH_VARARGS,
        ""
    },

    {
        "add_constraint",
        (PyCFunction)nvSpaceObject_add_constraint, METH_VARARGS,
        ""
    },

    {
        "remove",
        (PyCFunction)nvSpaceObject_remove, METH_VARARGS,
        ""
    },

    {
        "clear",
        (PyCFunction)nvSpaceObject_clear, METH_NOARGS,
        ""
    },

    {
        "set_shg",
        (PyCFunction)nvSpaceObject_set_shg, METH_VARARGS,
        ""
    },

    {
        "get_shg",
        (PyCFunction)nvSpaceObject_get_shg, METH_NOARGS,
        ""
    },

    {
        "set_kill_bounds",
        (PyCFunction)nvSpaceObject_set_kill_bounds, METH_VARARGS,
        ""
    },

    {NULL} // Sentinel
};

PyTypeObject nvSpaceObjectType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "nova.Space",
    .tp_doc = "Space object",
    .tp_basicsize = sizeof(nvSpaceObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = PyType_GenericNew,
    .tp_dealloc = (destructor)nvSpaceObject_dealloc,
    .tp_init = (initproc)nvSpaceObject_init,
    .tp_methods = nvSpaceObject_methods
};



/*  #######################################################

                            Module

    #######################################################  */



/**
 * Nova Physics method interface
*/
static PyMethodDef nova_methods[] = {
    {
        "create_circle",
        nv_create_circle, METH_VARARGS,
        ""
    },

    {
        "create_rect",
        nv_create_rect, METH_VARARGS,
        ""
    },

    {
        "create_polygon",
        nv_create_polygon, METH_VARARGS,
        ""
    },

    {NULL, NULL, 0, NULL} /* Sentinel */
};

/**
 * Nova Physics module interface
 */
static PyModuleDef nova_module = {
    PyModuleDef_HEAD_INIT,
    .m_name = "nova",
    .m_doc = "Nova Physics Engine",
    .m_size = -1,
    .m_methods = nova_methods
};

/**
 * Nova Physics module initializer
 */
PyMODINIT_FUNC PyInit_nova() {
    PyObject *m;

    if (PyType_Ready(&nvSpaceObjectType) < 0)
        return NULL;

    if (PyType_Ready(&nvBodyObjectType) < 0)
        return NULL;

    if (PyType_Ready(&nvVector2ObjectType) < 0)
        return NULL;

    if (PyType_Ready(&nvDistanceJointObjectType) < 0)
        return NULL;


    m = PyModule_Create(&nova_module);
    if (m == NULL)
        return NULL;

    /**
     * Add nova.Space
     */
    Py_INCREF(&nvSpaceObjectType);
    if (PyModule_AddObject(m, "Space", (PyObject *) &nvSpaceObjectType) < 0) {
        Py_DECREF(&nvSpaceObjectType);
        Py_DECREF(m);
        return NULL;
    }

    /**
     * Add nova.Body
     */
    Py_INCREF(&nvBodyObjectType);
    if (PyModule_AddObject(m, "Body", (PyObject *) &nvBodyObjectType) < 0) {
        Py_DECREF(&nvBodyObjectType);
        Py_DECREF(m);
        return NULL;
    }

    /**
     * Add nova.Vector2
     */
    Py_INCREF(&nvVector2ObjectType);
    if (PyModule_AddObject(m, "Vector2", (PyObject *) &nvVector2ObjectType) < 0) {
        Py_DECREF(&nvVector2ObjectType);
        Py_DECREF(m);
        return NULL;
    }

    /**
     * Add nova.DistanceJoint
     */
    Py_INCREF(&nvDistanceJointObjectType);
    if (PyModule_AddObject(m, "DistanceJoint", (PyObject *) &nvDistanceJointObjectType) < 0) {
        Py_DECREF(&nvDistanceJointObjectType);
        Py_DECREF(m);
        return NULL;
    }

    /* Add module constants */

    PyModule_AddStringConstant(m, "nova_version", NV_VERSTR);
    PyModule_AddStringConstant(m, "version", NOVA_PYTHON_VERSION);

    PyModule_AddIntConstant(m, "STATIC",  nvBodyType_STATIC);
    PyModule_AddIntConstant(m, "DYNAMIC", nvBodyType_DYNAMIC);

    return m;
}