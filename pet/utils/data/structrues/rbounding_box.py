# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved.
import torch
import numpy as np
# transpose
FLIP_LEFT_RIGHT = 0
FLIP_TOP_BOTTOM = 1


class RBoxList(object):
    """
    This class represents a set of bounding boxes.
    The bounding boxes are represented as a Nx4 Tensor.
    In order to uniquely determine the bounding boxes with respect
    to an image, we also store the corresponding image dimensions.
    They can contain extra information that is specific to each bounding box, such as
    labels.
    """

    def __init__(self, bbox, image_size, mode="xywha"):
        device = bbox.device if isinstance(bbox, torch.Tensor) else torch.device("cpu")
        bbox = torch.as_tensor(bbox, dtype=torch.float32, device=device)
        if bbox.ndimension() != 2:
            raise ValueError(
                "bbox should have 2 dimensions, got {}".format(bbox.ndimension())
            )
        if bbox.size(-1) != 5:
            raise ValueError(
                "last dimenion of bbox should have a "
                "size of 5, got {}".format(bbox.size(-1))
            )
        if mode not in ("xywha"):
            raise ValueError("mode should be 'xywha'")

        self.bbox = bbox
        self.size = image_size  # (image_width, image_height)
        self.mode = mode
        self.extra_fields = {}

    def add_field(self, field, field_data):
        self.extra_fields[field] = field_data

    def get_field(self, field):
        return self.extra_fields[field]

    def has_field(self, field):
        return field in self.extra_fields

    def fields(self):
        return list(self.extra_fields.keys())

    def _copy_extra_fields(self, bbox):
        for k, v in bbox.extra_fields.items():
            self.extra_fields[k] = v

    def rescale(self, boxes_margin, *args, **kwargs):
        """
        Returns a resized copy of this bounding box

        :param size: The requested size in pixels, as a 2-tuple:
            (width, height).
        """

        # ratios = tuple(float(s) / float(s_orig) for s, s_orig in zip(size, self.size))
        # assert np.abs(ratios[0] - ratios[1]) < 0.01, \
        #    'Need the ratios to be less than 0.001,' + str(ratios) + 'but tar/org' + str(size) + '/' + str(self.size)
        # ratio = ratios[0]
        scaled_xc, scaled_yc, scaled_w, scaled_h, scaled_a = self._split_into_xywha()
        # scaled_xc *= ratio
        # scaled_yc *= ratio
        scaled_w *= boxes_margin
        scaled_h *= boxes_margin
        # scaled_angle = a
        scaled_box = torch.cat(
            (scaled_xc, scaled_yc, scaled_w, scaled_h, scaled_a), dim=-1
        )
        bbox = RBoxList(scaled_box, self.size, mode=self.mode)
        # bbox._copy_extra_fields(self)
        for k, v in self.extra_fields.items():
            if not isinstance(v, torch.Tensor):
                # print(k)
                if  (not 'words' in k) and (not 'word_length' in k):
                    v = v.resize(self.size, *args, **kwargs)
            bbox.add_field(k, v)
        return bbox

    def resize(self, size, *args, **kwargs):
        """
        Returns a resized copy of this bounding box

        :param size: The requested size in pixels, as a 2-tuple:
            (width, height).
        """

        ratios = tuple(float(s) / float(s_orig) for s, s_orig in zip(size, self.size))
        assert np.abs(ratios[0] - ratios[1]) < 0.01, \
            'Need the ratios to be less than 0.001,' + str(ratios) + 'but tar/org' + str(size) + '/' + str(self.size)
        ratio = ratios[0]
        scaled_xc, scaled_yc, scaled_w, scaled_h, scaled_a = self._split_into_xywha()
        scaled_xc *= ratio
        scaled_yc *= ratio
        scaled_w *= ratio
        scaled_h *= ratio
        # scaled_angle = a
        scaled_box = torch.cat(
            (scaled_xc, scaled_yc, scaled_w, scaled_h, scaled_a), dim=-1
        )
        bbox = RBoxList(scaled_box, size, mode=self.mode)
        # bbox._copy_extra_fields(self)
        for k, v in self.extra_fields.items():
            if not isinstance(v, torch.Tensor):
                # print(k)
                if  (not 'words' in k) and (not 'word_length' in k):
                    v = v.resize(size, *args, **kwargs)
            bbox.add_field(k, v)
        return bbox

    def transpose(self, method):
        """
        Transpose bounding box (flip or rotate in 90 degree steps)
        :param method: One of :py:attr:`PIL.Image.FLIP_LEFT_RIGHT`,
          :py:attr:`PIL.Image.FLIP_TOP_BOTTOM`, :py:attr:`PIL.Image.ROTATE_90`,
          :py:attr:`PIL.Image.ROTATE_180`, :py:attr:`PIL.Image.ROTATE_270`,
          :py:attr:`PIL.Image.TRANSPOSE` or :py:attr:`PIL.Image.TRANSVERSE`.
        """
        '''
        if method not in (FLIP_LEFT_RIGHT, FLIP_TOP_BOTTOM):
            raise NotImplementedError(
                "Only FLIP_LEFT_RIGHT and FLIP_TOP_BOTTOM implemented"
            )

        image_width, image_height = self.size
        xmin, ymin, xmax, ymax = self._split_into_xyxy()
        if method == FLIP_LEFT_RIGHT:
            TO_REMOVE = 1
            transposed_xmin = image_width - xmax - TO_REMOVE
            transposed_xmax = image_width - xmin - TO_REMOVE
            transposed_ymin = ymin
            transposed_ymax = ymax
        elif method == FLIP_TOP_BOTTOM:
            transposed_xmin = xmin
            transposed_xmax = xmax
            transposed_ymin = image_height - ymax
            transposed_ymax = image_height - ymin

        transposed_boxes = torch.cat(
            (transposed_xmin, transposed_ymin, transposed_xmax, transposed_ymax), dim=-1
        )
        bbox = BoxList(transposed_boxes, self.size, mode="xyxy")
        # bbox._copy_extra_fields(self)
        for k, v in self.extra_fields.items():
            if not isinstance(v, torch.Tensor):
                v = v.transpose(method)
            bbox.add_field(k, v)
        return bbox.convert(self.mode)
        '''
    def crop(self, box):
        '''
        """
        Cropss a rectangular region from this bounding box. The box is a
        4-tuple defining the left, upper, right, and lower pixel
        coordinate.
        """
        xmin, ymin, xmax, ymax = self._split_into_xyxy()
        w, h = box[2] - box[0], box[3] - box[1]
        cropped_xmin = (xmin - box[0]).clamp(min=0, max=w)
        cropped_ymin = (ymin - box[1]).clamp(min=0, max=h)
        cropped_xmax = (xmax - box[0]).clamp(min=0, max=w)
        cropped_ymax = (ymax - box[1]).clamp(min=0, max=h)

        # TODO should I filter empty boxes here?
        if False:
            is_empty = (cropped_xmin == cropped_xmax) | (cropped_ymin == cropped_ymax)

        cropped_box = torch.cat(
            (cropped_xmin, cropped_ymin, cropped_xmax, cropped_ymax), dim=-1
        )
        bbox = BoxList(cropped_box, (w, h), mode="xyxy")
        # bbox._copy_extra_fields(self)
        for k, v in self.extra_fields.items():
            if not isinstance(v, torch.Tensor):
                v = v.crop(box)
            bbox.add_field(k, v)
        return bbox.convert(self.mode)
        '''
        return self
    # Tensor-like methods

    def to(self, device):
        bbox = RBoxList(self.bbox.to(device), self.size, self.mode)
        for k, v in self.extra_fields.items():
            if hasattr(v, "to"):
                v = v.to(device)
            bbox.add_field(k, v)
        return bbox

    def __getitem__(self, item):
        bbox = RBoxList(self.bbox[item], self.size, self.mode)
        for k, v in self.extra_fields.items():
            # print('bounding_box, k, v', k, v)
            bbox.add_field(k, v[item])
        return bbox

    def __len__(self):
        return self.bbox.shape[0]

    def _split_into_xywha(self):

        if self.mode == 'xywha':
            TO_REMOVE = 1
            xc, yc, w, h, a = self.bbox.split(1, dim=-1)
            return (
                xc, yc, w, h, a
            )
        else:
            raise RuntimeError("_split_into_xywha Should not be here")


    def clip_to_image(self, remove_empty=True):
        #TO_REMOVE = 1
        #self.bbox[:, 0].clamp_(min=0, max=self.size[0] - TO_REMOVE)
        #self.bbox[:, 1].clamp_(min=0, max=self.size[1] - TO_REMOVE)
        #self.bbox[:, 2].clamp_(min=0, max=self.size[0] - TO_REMOVE)
        #self.bbox[:, 3].clamp_(min=0, max=self.size[1] - TO_REMOVE)
        #if remove_empty:
        #    box = self.bbox
        #    keep = (box[:, 3] > box[:, 1]) & (box[:, 2] > box[:, 0])
        #    return self[keep]
        return self

    def area(self):
        box = self.bbox
        #if self.mode == "xyxy":
        #    TO_REMOVE = 1
        #    area = (box[:, 2] - box[:, 0] + TO_REMOVE) * (box[:, 3] - box[:, 1] + TO_REMOVE)
        if self.mode == "xywha":
            area = box[:, 2] * box[:, 3]
        else:
            raise RuntimeError("Should not be here", self.mode)

        return area

    def copy_with_fields(self, fields):
        bbox = RBoxList(self.bbox, self.size, self.mode)
        if not isinstance(fields, (list, tuple)):
            fields = [fields]
        for field in fields:
            bbox.add_field(field, self.get_field(field))
        return bbox

    def __repr__(self):
        s = self.__class__.__name__ + "("
        s += "num_boxes={}, ".format(len(self))
        s += "image_width={}, ".format(self.size[0])
        s += "image_height={}, ".format(self.size[1])
        s += "mode={})".format(self.mode)
        return s
