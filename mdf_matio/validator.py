from datetime import datetime
import json

import jsonschema


def _remove_nulls(data, skip=None):
    """Remove all null/None/empty values from a dict or list, except those listed in skip."""
    if isinstance(data, dict):
        new_dict = {}
        for key, val in data.items():
            new_val = _remove_nulls(val, skip=skip)
            if new_val is not None or (skip is not None and key in skip):
                new_dict[key] = new_val
        return new_dict
    elif isinstance(data, list):
        new_list = []
        for val in data:
            new_val = _remove_nulls(val, skip=skip)
            if new_val is not None:
                new_list.append(new_val)
        return new_list
    # Could delete required but empty blocks - services, etc.
    # elif hasattr(data, "__len__") and len(data) <= 0:
    #    return None
    else:
        return data


class ValidationError(Exception):
    """An Exception that indicates some part of the metadata did not validate
    successfully and should be revised."""
    # Defined here instead of a separate exceptions.py because
    # this is a single exception type, explicitly for the Validator
    pass


class MDFValidator():
    """Validates MDF feedstock.
    To use this tool, you must have properly-formatted MDF metadata,
    such as the metadata returned from a MatIO Extractor that has been run through
    an MDF Adapter.

    Example usage:
    (Given a dataset and validation info directly from MDF input, and records from Xtract)

    ```
    vald_obj = MDFValidator(schema_branch="master")
    vald_gen = vald_obj.validate_mdf_dataset(dataset, validation_info)
    dataset_entry = next(vald_gen)
    record_entries = []
    for r in records:
        record_entry = vald_gen.send(r)
        record.entries.append(record_entry)
    vald_gen.send(None)
    ```
    """
    def __init__(self, schema_branch="master"):
        """Create an MDFValidator.

        Arguments:
            schema_branch (str): The GitHub branch of the MDF schema to use in validation.
                    See https://github.com/materials-data-facility/data-schemas
        """
        self.__dataset = None
        self.__scroll_id = None
        self.__ingest_date = datetime.utcnow().isoformat("T") + "Z"
        self.__indexed_files = []
        self.ref_resolver = jsonschema.RefResolver("https://raw.githubusercontent.com/materials-"
                                                   "data-facility/data-schemas/{}/schemas/"
                                                   .format(schema_branch), None)

    def validate_mdf_dataset(self, ds_md, validation_info=None):
        """Begin validating a new dataset against the MDF schema.

        This function is a generator. You must initialize it with the following arguments,
        and then use `.send()` to send in single records to validate.
        The first yield value is the validated dataset entry.
        When you .send() a record, the yield value is the validated record.
        After you are finished sending records, you may send None to end the generator.
        Every record intended for MDF must be validated through this method.

        Arguments:
            ds_md (dict): The dataset metadata to validate.
            validation_info (dict): Additional validation configuration.
                project_blocks (list of str): The allowed "project" blocks. Default None.
                required_fields (list of str): Additional required fields not present
                        in the MDF schema. Default None.
                allowed_nulls (list of str): Fields allowed to be null/empty. Default None.
                base_acl (list of str): The ACL to set on entries. Default None,
                        which sets a public ACL.

        Yields:
            dict: Validated MDF-format metadata, ready for Search ingestion.
                    The first yield value is always the validated dataset entry.
                    When a record entry (dict) has been sent to the generator,
                    this will be the validated record entry.

        Accepts via .send():
            dict: A record to validate.
            None: Finish validating.
        """
        # Validate, save, and yield dataset
        dataset = self._validate_dataset(ds_md, validation_info)
        self.__dataset = dataset
        # Fetch first record
        record = yield dataset
        # Process all records the user has
        while record is not None:
            record = yield self._validate_record(record)
        # Yield once more to avoid forcing user to catch StopIteration
        # Effect is .send(None) returns None, which is logical
        yield

    def _validate_dataset(self, ds_md, validation_info=None):
        """Validate a dataset entry.
        Not intended for calling directly.

        Arguments:
            ds_md (dict): The dataset metadata to validate.
            validation_info (dict): Additional validation configuration.
                project_blocks (list of str): The allowed "project" blocks. Default None.
                required_fields (list of str): Additional required fields not present
                        in the MDF schema. Default None.
                allowed_nulls (list of str): Fields allowed to be null/empty. Default None.
                base_acl (list of str): The ACL to set on entries. Default None,
                        which sets a public ACL.

        Returns:
            dict: The validated dataset entry.
        """
        if validation_info is None:
            validation_info = {}
        self.__project_blocks = validation_info.get("project_blocks", None)
        self.__required_fields = validation_info.get("required_fields", None)
        self.__allowed_nulls = validation_info.get("allowed_nulls", None)
        self.__base_acl = validation_info.get("base_acl", None)

        # Load schema
        _, schema = self.ref_resolver.resolve("dataset.json")

        # if not ds_md.get("dc") or not isinstance(ds_md["dc"], dict):
        #    ds_md["dc"] = {}
        if not ds_md.get("mdf") or not isinstance(ds_md["mdf"], dict):
            ds_md["mdf"] = {}
        # if not ds_md.get("mrr") or not isinstance(ds_md["mrr"], dict):
        #     ds_md["mrr"] = {}

        # Add fields
        # BLOCK: dc
        # TODO

        # BLOCK: mdf
        # scroll_id
        self.__scroll_id = 0
        ds_md["mdf"]["scroll_id"] = self.__scroll_id
        self.__scroll_id += 1

        # ingest_date
        ds_md["mdf"]["ingest_date"] = self.__ingest_date

        # resource_type
        ds_md["mdf"]["resource_type"] = "dataset"

        # mdf-block fields source_id and source_name must already be set
        # (should be the case in correct preprocessing of submission)

        # acl
        if not ds_md["mdf"].get("acl"):
            ds_md["mdf"]["acl"] = self.__base_acl or ["public"]

        # version
        if not ds_md["mdf"].get("version"):
            ds_md["mdf"]["version"] = 1

        # BLOCK: mrr
        # TODO

        # Services
        ds_md["services"] = ds_md.get("services", {})

        # Data
        ds_md["data"] = ds_md.get("data", {})
        ds_md["data"]["total_size"] = 0

        # BLOCK: custom
        # Make all values into strings
        if ds_md.get("custom"):
            new_custom = {}
            for key, val in ds_md["custom"].items():
                new_custom[key] = str(val)
            ds_md["custom"] = new_custom

        # Require strict JSON
        try:
            json.dumps(ds_md, allow_nan=False)
        except (ValueError, json.JSONDecodeError) as e:
            raise ValidationError("Dataset metadata is not valid JSON: {}"
                                  .format(str(e))) from e

        # Remove null/None values
        ds_md = _remove_nulls(ds_md, self.__allowed_nulls)

        # Validate against schema
        try:
            jsonschema.validate(ds_md, schema, resolver=self.ref_resolver)
        except jsonschema.ValidationError as e:
            raise ValidationError("Invalid dataset metadata: {}"
                                  .format(str(e).split("\n")[0])) from e

        # Check projects blocks allowed
        # If no blocks, disallow projects
        if not self.__project_blocks:
            if ds_md.get("projects"):
                raise ValidationError("Unauthorized project metadata: No projects allowed")
        # If some project blocks allowed, check that only allowed ones are present
        else:
            unauthorized = []
            for proj in ds_md.get("projects", {}).keys():
                if proj not in self.__project_blocks:
                    unauthorized.append(proj)
            if unauthorized:
                raise ValidationError("Unauthorized project metadata: '{}' not allowed"
                                      .format(unauthorized))

        # Validate required fields
        # TODO: How should this validation be done?
        # The metadata conforms to the schema, there are just extra
        # `requires` values. Perhaps add these to the schema instead?
        # Lists, specifically, are an issue. Must all dicts in the list
        # conform? This behavior is difficult.
        # As a semi-temporary measure, only check the first element of lists.
        if self.__required_fields:
            missing = []
            for field_path in self.__required_fields:
                value = ds_md
                for field_name in field_path.split("."):
                    try:
                        value = value[field_name]
                        if isinstance(value, list) and len(value) > 0:
                            value = value[0]
                    except KeyError:
                        missing.append(field_path)
                        break
            if missing:
                raise ValidationError("Missing organization metadata: '{}' are required"
                                      .format(missing))

        # Ensure dataset JSON-sanitized before return
        return json.loads(json.dumps(ds_md))

    def _validate_record(self, rc_md):
        """Process and validate a record against the MDF schema.
        Not intented to be called directly.

        Arguments:
            rc_md (dict): The record metadata to validate.

        Returns:
            dict: The validated record.
        """
        if not self.__dataset:
            raise ValidationError("Dataset not started. Records cannot be validated without "
                                  "a dataset. Call .validate_mdf_dataset() instead.")

        # Load schema
        _, schema = self.ref_resolver.resolve("record.json")

        # Add any missing blocks
        if not rc_md.get("mdf"):
            rc_md["mdf"] = {}
        if not rc_md.get("files"):
            rc_md["files"] = []
        elif isinstance(rc_md["files"], dict):
            rc_md["files"] = [rc_md["files"]]
        if not rc_md.get("material"):
            rc_md["material"] = {}

        # Add fields
        # BLOCK: mdf
        # source_id
        rc_md["mdf"]["source_id"] = self.__dataset["mdf"]["source_id"]

        # source_name
        rc_md["mdf"]["source_name"] = self.__dataset["mdf"]["source_name"]

        # scroll_id
        rc_md["mdf"]["scroll_id"] = self.__scroll_id
        self.__scroll_id += 1

        # ingest_date
        rc_md["mdf"]["ingest_date"] = self.__ingest_date

        # resource_type
        rc_md["mdf"]["resource_type"] = "record"

        # version
        rc_md["mdf"]["version"] = self.__dataset["mdf"]["version"]

        # acl
        if not rc_md["mdf"].get("acl"):
            rc_md["mdf"]["acl"] = self.__base_acl or self.__dataset["mdf"]["acl"]

        # organizations
        if self.__dataset["mdf"].get("organizations"):
            rc_md["mdf"]["organizations"] = self.__dataset["mdf"]["organizations"]

        # BLOCK: files
        # Add file data to dataset
        if rc_md["files"]:
            self.__indexed_files += rc_md["files"]
            for f in rc_md["files"]:
                self.__dataset["data"]["total_size"] += f.get("length", 0)

        # BLOCK: material
        # elements
        if rc_md["material"].get("composition"):
            composition = rc_md["material"]["composition"].replace("and", "")
            str_of_elem = ""
            for char in list(composition):
                if char.isupper():  # Start of new element symbol
                    str_of_elem += " " + char
                elif char.islower():  # Continuation of symbol
                    str_of_elem += char
                # Anything else is not an element (numbers, whitespace, etc.)

            # Split elements in string (on whitespace), make unique and JSON-serializable
            list_of_elem = list(set(str_of_elem.split()))
            # Ensure deterministic results
            list_of_elem.sort()

            rc_md["material"]["elements"] = list_of_elem
        elif rc_md["material"].get("elemental_proportions"):
            rc_md["material"]["elements"] = list(rc_md["material"]["elemental_proportions"].keys())
            rc_md["material"]["elements"].sort()

        # BLOCK: custom
        # Make all values into strings
        if rc_md.get("custom"):
            new_custom = {}
            for key, val in rc_md["custom"].items():
                new_custom[key] = str(val)
            rc_md["custom"] = new_custom

        # Require strict JSON
        try:
            json.dumps(rc_md, allow_nan=False)
        except (ValueError, json.JSONDecodeError) as e:
            raise ValidationError("Record is not valid JSON: {}".format(str(e))) from e

        # Remove null/None values
        rc_md = _remove_nulls(rc_md, self.__allowed_nulls)

        # Validate against schema
        try:
            jsonschema.validate(rc_md, schema, resolver=self.ref_resolver)
        except jsonschema.ValidationError as e:
            raise ValidationError("Invalid record metadata: {}"
                                  .format(str(e).split("\n")[0])) from e

        # Return results
        return rc_md
