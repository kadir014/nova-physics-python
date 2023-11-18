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
} nv_Vector2Object;

/**
 * Body object interface
 */
typedef struct {
    PyObject_HEAD
    nv_Body *body;
    nv_BodyType type;
    int shape;
    nv_Vector2Object *position;
    double angle;
    double radius;
    nv_uint16 id;
} nv_BodyObject;

/**
 * Space object interface
 */
typedef struct {
    PyObject_HEAD
    nv_Space *space;
    nv_Array *body_objects;
} nv_SpaceObject;

/**
 * Distance Joint Constraint object interface
 */
typedef struct {
    PyObject_HEAD
    nv_Constraint *cons;
    double length;
} nv_DistanceJointObject;



/*  #######################################################

                          Vector2

    #######################################################  */



/**
 * Create new Vector2 object
 */
nv_Vector2Object *nv_Vector2Object_new(double x, double y);

/**
 * Vector2 Python object to Vector2 struct
 */
#define PY_TO_VEC2(o) (NV_VEC2((o)->x, (o)->y))



static void nv_Vector2Object_dealloc(nv_Vector2Object *self) {
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static int nv_Vector2Object_init(
    nv_Vector2Object *self,
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


static PyObject *nv_Vector2Object___repr__(nv_Vector2Object* self) {
    return PyUnicode_FromFormat("<Vector2(%g, %g)>", self->x, self->y);
}


/**
 * Vector2 object method interface
 */
static PyMethodDef nv_Vector2Object_methods[] = {
    {
        "__repr__",
        (PyCFunction)nv_Vector2Object___repr__, METH_NOARGS,
        ""
    },

    {NULL} // Sentinel
};

static PyObject *nv_Vector2Object___add__(
    nv_Vector2Object *self,
    nv_Vector2Object *vector
) {
    nv_Vector2 result = nv_Vector2_add(PY_TO_VEC2(self), PY_TO_VEC2(vector));

    return nv_Vector2Object_new(result.x, result.y);
}

static PyObject *nv_Vector2Object___sub__(
    nv_Vector2Object *self,
    nv_Vector2Object *vector
) {
    nv_Vector2 result = nv_Vector2_sub(PY_TO_VEC2(self), PY_TO_VEC2(vector));

    return nv_Vector2Object_new(result.x, result.y);
}

static PyObject *nv_Vector2Object___mul__(
    nv_Vector2Object *self,
    PyObject *scalar
) {
    double s = PyFloat_AS_DOUBLE(scalar);

    nv_Vector2 result = nv_Vector2_mul(PY_TO_VEC2(self), s);

    return nv_Vector2Object_new(result.x, result.y);
}

static PyObject *nv_Vector2Object___truediv__(
    nv_Vector2Object *self,
    PyObject *scalar
) {
    double s = PyFloat_AS_DOUBLE(scalar);

    nv_Vector2 result = nv_Vector2_div(PY_TO_VEC2(self), s);

    return nv_Vector2Object_new(result.x, result.y);
}

/**
 * Vector2 object operator overloadings
 */
static PyNumberMethods nv_Vector2Object_operators = {
    .nb_add =         (binaryfunc)nv_Vector2Object___add__,
    .nb_subtract =    (binaryfunc)nv_Vector2Object___sub__,
    .nb_multiply =    (binaryfunc)nv_Vector2Object___mul__,
    .nb_true_divide = (binaryfunc)nv_Vector2Object___truediv__
};

/**
 * Vector2 object member interface
 */
static PyMemberDef nv_Vector2Object_members[] = {
    {
        "x",
        T_DOUBLE, offsetof(nv_Vector2Object, x), 0,
        ""
    },

    {
        "y",
        T_DOUBLE, offsetof(nv_Vector2Object, y), 0,
        ""
    },

    {NULL} // Sentinel
};

/**
 * Vector2 object type internals
 */
PyTypeObject nv_Vector2ObjectType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "nova.Vector2",
    .tp_doc = "Vector2 object",
    .tp_basicsize = sizeof(nv_Vector2Object),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = PyType_GenericNew,
    .tp_dealloc = (destructor)nv_Vector2Object_dealloc,
    .tp_init = (initproc)nv_Vector2Object_init,
    .tp_members = nv_Vector2Object_members,
    .tp_as_number = &nv_Vector2Object_operators,
    .tp_str = nv_Vector2Object___repr__
};

nv_Vector2Object *nv_Vector2Object_new(double x, double y) {
    PyObject *args = Py_BuildValue("dd", x, y);
    nv_Vector2Object *obj = (nv_Vector2Object *)PyObject_CallObject((PyObject *)&nv_Vector2ObjectType, args);
    Py_DECREF(args);
    Py_INCREF(obj);
    return obj;
}



/*  #######################################################

                             Body

    #######################################################  */



static void nv_BodyObject_dealloc(nv_BodyObject *self) {
    // Don't free nv_Body instance because space frees it
    Py_XDECREF(self->position);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static int nv_BodyObject_init(
    nv_BodyObject *self,
    PyObject *args,
    PyObject *kwds
) {
    nv_BodyType type;
    int shape;
    double x;
    double y;
    double angle;
    double density;
    double restitution;
    double friction;
    double radius;
    PyObject *vertices = NULL;

    if (!PyArg_ParseTuple(
        args, "iiddddddd|O",
        &type, &shape, &x, &y, &angle, &density, &restitution, &friction, &radius, &vertices
    ))
        return -1;

    self->type = type;
    self->shape = shape;
    self->position = (nv_Vector2Object *)nv_Vector2Object_new(x, y);
    self->angle = angle;
    self->radius = radius;

    nv_Array *new_vertices = NULL;

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

        // Create nv_Array from vertices sequence
        new_vertices = nv_Array_new();
        PyObject *v;
        PyObject *vx;
        PyObject *vy;

        for (size_t i = 0; i < vertices_len; i++) {
            v = PySequence_GetItem(vertices, i);
            vx = PySequence_GetItem(v, 0);
            vy = PySequence_GetItem(v, 1);

            nv_Array_add(new_vertices, NV_VEC2_NEW(PyFloat_AS_DOUBLE(vx), PyFloat_AS_DOUBLE(vy)));

            Py_DECREF(v);
            Py_DECREF(vx);
            Py_DECREF(vy);
        }
    }

    if (shape == 0) {
        self->body = nv_Circle_new(
            type,
            NV_VEC2(x, y),
            angle,
            (nv_Material){density, restitution, friction},
            radius
        );
    }

    else if (shape == 1) {
        self->body = nv_Polygon_new(
            type,
            NV_VEC2(x, y),
            angle,
            (nv_Material){density, restitution, friction},
            new_vertices
        );
    }

    // Actual ID is assigned at adding to space
    self->id = 0;

    return 0;
}

/**
 * Body object member interface
 */
static PyMemberDef nv_BodyObject_members[] = {
    {
        "type",
        T_INT, offsetof(nv_BodyObject, type), 0,
        ""
    },

    {
        "shape",
        T_INT, offsetof(nv_BodyObject, shape), 0,
        ""
    },

    {
        "position",
        T_OBJECT_EX, offsetof(nv_BodyObject, position), 0,
        ""
    },

    {
        "angle",
        T_DOUBLE, offsetof(nv_BodyObject, angle), 0,
        ""
    },

    {
        "radius",
        T_DOUBLE, offsetof(nv_BodyObject, radius), 0,
        ""
    },

    {
        "id",
        T_INT, offsetof(nv_BodyObject, id), 0,
        ""
    },

    {NULL} // Sentinel
};

static PyObject *nv_BodyObject_get_vertices(
    nv_BodyObject *self,
    PyObject *Py_UNUSED(ignored)
) {
    nv_Polygon_model_to_world(self->body);
    PyObject *return_tup = PyTuple_New(self->body->shape->trans_vertices->size);

    for (size_t i = 0; i < self->body->shape->trans_vertices->size; i++) {
        nv_Vector2 v = NV_TO_VEC2(self->body->shape->trans_vertices->data[i]);

        PyTuple_SET_ITEM(return_tup, i, (PyObject *)nv_Vector2Object_new(v.x, v.y));
    }

    return return_tup;
}

static PyObject *nv_BodyObject_get_aabb(
    nv_BodyObject *self,
    PyObject *Py_UNUSED(ignored)
) {
    PyObject *return_tup = PyTuple_New(4);

    nv_AABB aabb = nv_Body_get_aabb(self->body);

    PyTuple_SET_ITEM(return_tup, 0, PyFloat_FromDouble(aabb.min_x));
    PyTuple_SET_ITEM(return_tup, 1, PyFloat_FromDouble(aabb.min_y));
    PyTuple_SET_ITEM(return_tup, 2, PyFloat_FromDouble(aabb.max_x));
    PyTuple_SET_ITEM(return_tup, 3, PyFloat_FromDouble(aabb.max_y));

    return return_tup;
}

static PyObject *nv_BodyObject_apply_force(
    nv_BodyObject *self,
    PyObject *args
) {
    nv_Vector2Object *force;

    if (!PyArg_ParseTuple(args, "O!", &nv_Vector2ObjectType, &force))
        return NULL;

    nv_Body_apply_force(self->body, NV_VEC2(force->x, force->y));

    Py_RETURN_NONE;
}

static PyObject *nv_BodyObject_apply_force_at(
    nv_BodyObject *self,
    PyObject *args
) {
    nv_Vector2Object *force;
    nv_Vector2Object *position;

    if (!PyArg_ParseTuple(args, "O!O!", &nv_Vector2ObjectType, &force, &nv_Vector2ObjectType, &position))
        return NULL;

    nv_Body_apply_force_at(self->body, NV_VEC2(force->x, force->y), NV_VEC2(position->x, position->y));

    Py_RETURN_NONE;
}

static PyObject *nv_BodyObject_apply_impulse(
    nv_BodyObject *self,
    PyObject *args
) {
    nv_Vector2Object *force;
    nv_Vector2Object *position;

    if (!PyArg_ParseTuple(args, "O!O!", &nv_Vector2ObjectType, &force, &nv_Vector2ObjectType, &position))
        return NULL;

    nv_Body_apply_impulse(self->body, NV_VEC2(force->x, force->y), NV_VEC2(position->x, position->y));

    Py_RETURN_NONE;
}

static PyObject *nv_BodyObject_set_mass(
    nv_BodyObject *self,
    PyObject *args
) {
    double mass;

    if (!PyArg_ParseTuple(args, "d", &mass))
        return NULL;

    nv_Body_set_mass(self->body, mass);

    Py_RETURN_NONE;
}

static PyObject *nv_BodyObject_get_mass(
    nv_BodyObject *self,
    PyObject *Py_UNUSED(ignored)
) {
    return PyFloat_FromDouble(self->body->mass);
}

static PyObject *nv_BodyObject_set_inertia(
    nv_BodyObject *self,
    PyObject *args
) {
    double inertia;

    if (!PyArg_ParseTuple(args, "d", &inertia))
        return NULL;

    nv_Body_set_inertia(self->body, inertia);

    Py_RETURN_NONE;
}

static PyObject *nv_BodyObject_get_inertia(
    nv_BodyObject *self,
    PyObject *Py_UNUSED(ignored)
) {
    return PyFloat_FromDouble(self->body->inertia);
}

static PyObject *nv_BodyObject_set_position(
    nv_BodyObject *self,
    PyObject *args
) {
    nv_Vector2Object *position;

    if (!PyArg_ParseTuple(args, "O!", &nv_Vector2ObjectType, &position))
        return NULL;

    self->body->position = NV_VEC2(position->x, position->y);
    self->position->x = self->body->position.x;
    self->position->y = self->body->position.y; 

    Py_RETURN_NONE;
}

static PyObject *nv_BodyObject_set_collision(
    nv_BodyObject *self,
    PyObject *args
) {
    unsigned char collision;

    if (!PyArg_ParseTuple(args, "b", &collision))
        return NULL;

    self->body->enable_collision = collision;

    Py_RETURN_NONE;
}

/**
 * Body object method interface
 */
static PyMethodDef nv_BodyObject_methods[] = {
    {
        "get_vertices",
        (PyCFunction)nv_BodyObject_get_vertices, METH_NOARGS,
        ""
    },

    {
        "get_aabb",
        (PyCFunction)nv_BodyObject_get_aabb, METH_NOARGS,
        ""
    },

    {
        "apply_force",
        (PyCFunction)nv_BodyObject_apply_force, METH_VARARGS,
        ""
    },

    {
        "apply_force_at",
        (PyCFunction)nv_BodyObject_apply_force_at, METH_VARARGS,
        ""
    },

    {
        "apply_impulse",
        (PyCFunction)nv_BodyObject_apply_impulse, METH_VARARGS,
        ""
    },

    {
        "set_mass",
        (PyCFunction)nv_BodyObject_set_mass, METH_VARARGS,
        ""
    },

    {
        "get_mass",
        (PyCFunction)nv_BodyObject_get_mass, METH_NOARGS,
        ""
    },

    {
        "set_inertia",
        (PyCFunction)nv_BodyObject_set_inertia, METH_VARARGS,
        ""
    },

    {
        "get_inertia",
        (PyCFunction)nv_BodyObject_get_inertia, METH_NOARGS,
        ""
    },

    {
        "set_position",
        (PyCFunction)nv_BodyObject_set_position, METH_VARARGS,
        ""
    },

    {
        "set_collision",
        (PyCFunction)nv_BodyObject_set_collision, METH_VARARGS,
        ""
    },

    {NULL} // Sentinel
};

PyTypeObject nv_BodyObjectType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "nova.Body",
    .tp_doc = "Body object",
    .tp_basicsize = sizeof(nv_BodyObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = PyType_GenericNew,
    .tp_dealloc = (destructor)nv_BodyObject_dealloc,
    .tp_init = (initproc)nv_BodyObject_init,
    .tp_methods = nv_BodyObject_methods,
    .tp_members = nv_BodyObject_members
};


PyObject *nv_create_circle(PyObject *self, PyObject *args) {
    nv_BodyType type;
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
    nv_BodyObject *obj = (nv_BodyObject *)PyObject_CallObject((PyObject *)&nv_BodyObjectType, inst_args);
    Py_DECREF(inst_args);
    return (PyObject *)obj;
}

PyObject *nv_create_rect(PyObject *self, PyObject *args) {
    nv_BodyType type;
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

    nv_BodyObject *obj = (nv_BodyObject *)PyObject_CallObject((PyObject *)&nv_BodyObjectType, inst_args);
    Py_DECREF(inst_args);
    return (PyObject *)obj;
}



/*  #######################################################

                  Distance Join Constraint

    #######################################################  */



static void nv_DistanceJointObject_dealloc(nv_DistanceJointObject *self) {
    // Don't free constraint ecause space frees it
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static int nv_DistanceJointObject_init(
    nv_DistanceJointObject *self,
    PyObject *args,
    PyObject *kwds
) {
    nv_BodyType type;
    int shape;
    double x;
    double y;
    double angle;
    double density;
    double restitution;
    double friction;
    double radius;
    PyObject *vertices = NULL;

    nv_BodyObject *a = NULL;
    nv_BodyObject *b = NULL;
    nv_Vector2Object *anchor_a = NULL;
    nv_Vector2Object *anchor_b = NULL;
    double length;

    if (!PyArg_ParseTuple(
        args, "O!O!O!O!d",
        &nv_BodyObjectType, &a,
        &nv_BodyObjectType, &b,
        &nv_Vector2ObjectType, &anchor_a,
        &nv_Vector2ObjectType, &anchor_b,
        &length
    ))
        return -1;
    
    self->cons = nv_DistanceJoint_new(
        a->body, b->body, PY_TO_VEC2(anchor_a), PY_TO_VEC2(anchor_b), length
    );

    return 0;
}

/**
 * Distance joint object member interface
 */
static PyMemberDef nv_DistanceJointObject_members[] = {
    {
        "length",
        T_DOUBLE, offsetof(nv_DistanceJointObject, length), 0,
        ""
    },

    {NULL} // Sentinel
};

PyTypeObject nv_DistanceJointObjectType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "nova.DistanceJoint",
    .tp_doc = "Distance joint constraintt",
    .tp_basicsize = sizeof(nv_DistanceJointObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = PyType_GenericNew,
    .tp_dealloc = (destructor)nv_DistanceJointObject_dealloc,
    .tp_init = (initproc)nv_DistanceJointObject_init,
    .tp_members = nv_DistanceJointObject_members
};



/*  #######################################################

                            Space

    #######################################################  */



static void nv_SpaceObject_dealloc(nv_SpaceObject *self) {
    nv_Space_free(self->space);

    // Decrease reference of each body object in array
    for (size_t i = 0; i < self->body_objects->size; i++) {
        PyObject *body = (PyObject *)self->body_objects->data[i];
        Py_DECREF(body);
    }

    nv_Array_free(self->body_objects);

    Py_TYPE(self)->tp_free((PyObject *) self);
}

static int nv_SpaceObject_init(
    nv_SpaceObject *self,
    PyObject *args,
    PyObject *kwds
) {
    self->space = nv_Space_new();
    self->body_objects = nv_Array_new();

    return 0;
}

static PyObject *nv_SpaceObject_step(
    nv_SpaceObject *self,
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

    nv_Space_step(
        self->space,
        dt,
        velocity_iters,
        position_iters,
        constraint_iters,
        substeps
    );

    nv_Array *removed = nv_Array_new();

    for (size_t i = 0; i < self->body_objects->size; i++) {
        nv_BodyObject *body_object = (nv_BodyObject *)self->body_objects->data[i];

        bool found = false;
        nv_Body *found_body;
        for (size_t j = 0; j < self->space->bodies->size; j++) {
            nv_Body *body = (nv_Body *)self->space->bodies->data[j];
            if (body == body_object->body) {
                found = true;
                found_body = body;
                break;
            }
        }

        if (!found) {
            nv_Array_add(removed, body_object);
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
        nv_BodyObject *body_object = removed->data[i];
        Py_DECREF(body_object);
        nv_Array_remove(self->body_objects, body_object);
    }

    Py_RETURN_NONE;
}

static PyObject *nv_SpaceObject_get_bodies(
    nv_SpaceObject *self,
    PyObject *Py_UNUSED(ignored)
) {
    PyObject *return_tup = PyTuple_New(self->body_objects->size);

    for (size_t i = 0; i < self->body_objects->size; i++) {
        nv_BodyObject *body = (nv_BodyObject *)self->body_objects->data[i];
        
        Py_INCREF(body);
        PyTuple_SET_ITEM(return_tup, i, body);
    }

    return return_tup;
}

static PyObject *nv_SpaceObject_add(
    nv_SpaceObject *self,
    PyObject *args
) {
    nv_BodyObject *body;

    if (!PyArg_ParseTuple(args, "O!", &nv_BodyObjectType, &body))
        return NULL;

    nv_Space_add(self->space, body->body);
    body->id = body->body->id;
    Py_INCREF(body);
    nv_Array_add(self->body_objects, body);

    Py_RETURN_NONE;
}

static PyObject *nv_SpaceObject_add_constraint(
    nv_SpaceObject *self,
    PyObject *args
) {
    PyObject *constraint;

    if (!PyArg_ParseTuple(args, "O", &constraint))
        return NULL;

    if (PyObject_IsInstance(constraint, (PyObject *)(&nv_DistanceJointObjectType)))
        nv_Space_add_constraint(self->space, ((nv_DistanceJointObject *)constraint)->cons);

    Py_RETURN_NONE;
}

static PyObject *nv_SpaceObject_remove(
    nv_SpaceObject *self,
    PyObject *args
) {
    nv_BodyObject *body;

    if (!PyArg_ParseTuple(args, "O!", &nv_BodyObjectType, &body))
        return NULL;

    nv_Space_remove(self->space, body->body);
    nv_Array_remove(self->body_objects, body);
    Py_XDECREF(body);

    Py_RETURN_NONE;
}

static PyObject *nv_SpaceObject_clear(
    nv_SpaceObject *self,
    PyObject *Py_UNUSED(ignored)
) {
    while (self->body_objects->size > 0) {
        nv_BodyObject *body_obj = (nv_BodyObject *)nv_Array_pop(self->body_objects, 0);
        Py_DECREF(body_obj);
    }

    nv_Space_clear(self->space);

    Py_RETURN_NONE;
}

static PyObject *nv_SpaceObject_set_shg(
    nv_SpaceObject *self,
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

    nv_Space_set_SHG(
        self->space,
        (nv_AABB){min_x, min_y, max_x, max_y},
        cell_width,
        cell_height
    );

    Py_RETURN_NONE;
}

static PyObject *nv_SpaceObject_get_shg(
    nv_SpaceObject *self,
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

static PyObject *nv_SpaceObject_set_kill_bounds(
    nv_SpaceObject *self,
    PyObject *args
) {
    double min_x;
    double min_y;
    double max_x;
    double max_y;

    if (!PyArg_ParseTuple(args, "dddd", &min_x, &min_y, &max_x, &max_y))
        return NULL;

    self->space->kill_bounds = (nv_AABB){min_x, min_y, max_x, max_y};

    Py_RETURN_NONE;
}

/**
 * Space object method interface
 */
static PyMethodDef nv_SpaceObject_methods[] = {
    {
        "step",
        (PyCFunction)nv_SpaceObject_step, METH_VARARGS,
        ""
    },

    {
        "get_bodies",
        (PyCFunction)nv_SpaceObject_get_bodies, METH_NOARGS,
        ""
    },

    {
        "add",
        (PyCFunction)nv_SpaceObject_add, METH_VARARGS,
        ""
    },

    {
        "add_constraint",
        (PyCFunction)nv_SpaceObject_add_constraint, METH_VARARGS,
        ""
    },

    {
        "remove",
        (PyCFunction)nv_SpaceObject_remove, METH_VARARGS,
        ""
    },

    {
        "clear",
        (PyCFunction)nv_SpaceObject_clear, METH_NOARGS,
        ""
    },

    {
        "set_shg",
        (PyCFunction)nv_SpaceObject_set_shg, METH_VARARGS,
        ""
    },

    {
        "get_shg",
        (PyCFunction)nv_SpaceObject_get_shg, METH_NOARGS,
        ""
    },

    {
        "set_kill_bounds",
        (PyCFunction)nv_SpaceObject_set_kill_bounds, METH_VARARGS,
        ""
    },

    {NULL} // Sentinel
};

PyTypeObject nv_SpaceObjectType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "nova.Space",
    .tp_doc = "Space object",
    .tp_basicsize = sizeof(nv_SpaceObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = PyType_GenericNew,
    .tp_dealloc = (destructor)nv_SpaceObject_dealloc,
    .tp_init = (initproc)nv_SpaceObject_init,
    .tp_methods = nv_SpaceObject_methods
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
        "Create a body with circle shape."
    },

    {
        "create_rect",
        nv_create_rect, METH_VARARGS,
        "Create a body with rect (polygon) shape."
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

    if (PyType_Ready(&nv_SpaceObjectType) < 0)
        return NULL;

    if (PyType_Ready(&nv_BodyObjectType) < 0)
        return NULL;

    if (PyType_Ready(&nv_Vector2ObjectType) < 0)
        return NULL;

    if (PyType_Ready(&nv_DistanceJointObjectType) < 0)
        return NULL;


    m = PyModule_Create(&nova_module);
    if (m == NULL)
        return NULL;

    /**
     * Add nova.Space
     */
    Py_INCREF(&nv_SpaceObjectType);
    if (PyModule_AddObject(m, "Space", (PyObject *) &nv_SpaceObjectType) < 0) {
        Py_DECREF(&nv_SpaceObjectType);
        Py_DECREF(m);
        return NULL;
    }

    /**
     * Add nova.Body
     */
    Py_INCREF(&nv_BodyObjectType);
    if (PyModule_AddObject(m, "Body", (PyObject *) &nv_BodyObjectType) < 0) {
        Py_DECREF(&nv_BodyObjectType);
        Py_DECREF(m);
        return NULL;
    }

    /**
     * Add nova.Vector2
     */
    Py_INCREF(&nv_Vector2ObjectType);
    if (PyModule_AddObject(m, "Vector2", (PyObject *) &nv_Vector2ObjectType) < 0) {
        Py_DECREF(&nv_Vector2ObjectType);
        Py_DECREF(m);
        return NULL;
    }

    /**
     * Add nova.DistanceJoint
     */
    Py_INCREF(&nv_DistanceJointObjectType);
    if (PyModule_AddObject(m, "DistanceJoint", (PyObject *) &nv_DistanceJointObjectType) < 0) {
        Py_DECREF(&nv_DistanceJointObjectType);
        Py_DECREF(m);
        return NULL;
    }

    /* Add module constants */

    PyModule_AddStringConstant(m, "nova_version", NV_VERSTR);
    PyModule_AddStringConstant(m, "version", NOVA_PYTHON_VERSION);

    PyModule_AddIntConstant(m, "STATIC",  nv_BodyType_STATIC);
    PyModule_AddIntConstant(m, "DYNAMIC", nv_BodyType_DYNAMIC);

    return m;
}